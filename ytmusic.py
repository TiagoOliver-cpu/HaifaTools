"""Integração com o YouTube Music (ytmusicapi).

Autenticação (necessária só para criar playlists; a busca funciona sem login):
  - variável de ambiente YTMUSIC_AUTH com o conteúdo do browser.json, ou
  - arquivo browser.json na pasta do projeto (apenas para testes locais).
"""
import json
import os
import re
import unicodedata
from difflib import SequenceMatcher

from ytmusicapi import YTMusic

LIMIAR_ARTISTA = 0.75        # artista do resultado precisa bater com o da playlist
LIMIAR_MATCH = 0.62          # abaixo disso a faixa é considerada "não encontrada"
TOLERANCIA_DURACAO_S = 25    # diferença de duração que ainda conta como mesma faixa


def _cliente(autenticado=False):
    bruto = os.environ.get("YTMUSIC_AUTH")
    if bruto:
        return YTMusic(json.loads(bruto))
    if os.path.exists("browser.json"):
        return YTMusic("browser.json")
    if autenticado:
        raise RuntimeError(
            "Credenciais do YouTube Music não encontradas. "
            "Defina a variável YTMUSIC_AUTH com o conteúdo do browser.json."
        )
    return YTMusic()


def _norm(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", texto)   # tira (ao vivo), [live]...
    texto = re.sub(r"[^a-z0-9 ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _sim(a, b):
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return max(0.85, SequenceMatcher(None, a, b).ratio())
    return SequenceMatcher(None, a, b).ratio()


def _nomes(texto):
    partes = re.split(r",|&|\bfeat\.?|\bft\.?|\be\b|\bcom\b|\bx\b", texto or "", flags=re.IGNORECASE)
    return [p.strip() for p in partes if p.strip()]


def _sim_artista(artistas_resultado, artista):
    """Cobertura média: cada artista esperado precisa aparecer entre os do resultado."""
    esperados = _nomes(artista)
    achados = [a.get("name", "") for a in artistas_resultado or []]
    if not esperados or not achados:
        return 0.0
    notas = [max(_sim(e, a) for a in achados) for e in esperados]
    return sum(notas) / len(notas)


def _pontuar_orientacao(resultado, musica, artista, duracao_s):
    """Nota do resultado, ou None se o artista não bate (regra obrigatória)."""
    conhecido = bool(artista) and artista != "Desconhecido"
    s_artista = _sim_artista(resultado.get("artists"), artista) if conhecido else 0.5
    if conhecido and s_artista < LIMIAR_ARTISTA:
        return None
    s_titulo = _sim(resultado.get("title"), musica)
    nota = 0.6 * s_titulo + 0.4 * s_artista
    dur = resultado.get("duration_seconds")
    if duracao_s and dur:
        nota += 0.08 if abs(dur - duracao_s) <= TOLERANCIA_DURACAO_S else -0.12
    return nota


def _pontuar(resultado, faixa):
    nota = _pontuar_orientacao(resultado, faixa["musica"], faixa["artista"], faixa.get("duracao_s"))
    if faixa.get("confianca") == "baixa":
        # Parser incerto sobre quem é artista e quem é música: testa também invertido.
        troca = _pontuar_orientacao(resultado, faixa["artista"], faixa["musica"], faixa.get("duracao_s"))
        if troca is not None and (nota is None or troca > nota):
            nota = troca
    return nota


def buscar_faixa(yt, faixa):
    """Procura a melhor correspondência para uma faixa vinda do parser.

    Retorna dict {video_id, titulo, artistas, nota, origem} ou None.
    """
    melhor = None
    consultas = faixa.get("candidatos") or [f"{faixa['artista']} {faixa['musica']}"]
    erros = []
    for consulta in consultas:
        try:
            resultados = yt.search(consulta, filter="songs", limit=5)
        except Exception as e:
            erros.append(e)
            continue
        for r in resultados:
            if not r.get("videoId"):
                continue
            nota = _pontuar(r, faixa)
            if nota is None:
                continue          # artista não confere: descarta o resultado
            if melhor is None or nota > melhor["nota"]:
                melhor = {
                    "video_id": r["videoId"],
                    "titulo": r.get("title"),
                    "artistas": ", ".join(a.get("name", "") for a in r.get("artists") or []),
                    "nota": round(nota, 3),
                    "origem": "busca",
                }
        if melhor and melhor["nota"] >= 0.85:    # já está bom, não gasta mais buscas
            break
    if len(erros) == len(consultas):
        # Todas as buscas falharam: é problema de rede/bloqueio, não "faixa inexistente".
        raise RuntimeError(f"Falha ao buscar no YouTube Music: {erros[-1]}")
    if melhor and melhor["nota"] >= LIMIAR_MATCH:
        return melhor
    return None


def escolher_faixa(yt, faixa, fallback_video_original=True):
    """Decide qual vídeo/faixa entra na playlist.

    Medleys (várias músicas num vídeo só) usam SEMPRE o vídeo original: uma busca
    poderia trazer só uma das músicas, e o objetivo é manter a faixa com as duas.
    """
    video_original = None
    if fallback_video_original and faixa.get("video_id"):
        video_original = {"video_id": faixa["video_id"], "titulo": faixa["titulo_original"],
                          "artistas": faixa.get("canal") or "", "nota": 0.0,
                          "origem": "video_original"}
    if faixa.get("medley") and video_original:
        return video_original
    return buscar_faixa(yt, faixa) or video_original


def criar_playlist_ytmusic(faixas, nome, descricao="", privacidade="UNLISTED",
                           fallback_video_original=True):
    """Procura cada faixa e cria a playlist.

    Se não achar a versão "song", usa o vídeo original do YouTube (marcado como
    origem='video_original') para a playlist não perder faixas.
    Retorna dict com link, contagens e a lista detalhada de resultados.
    """
    yt_busca = _cliente(autenticado=False)
    detalhes, ids, vistos = [], [], set()

    for faixa in faixas:
        achado = escolher_faixa(yt_busca, faixa, fallback_video_original)
        detalhes.append({"original": faixa["titulo_original"], "resultado": achado})
        if achado and achado["video_id"] not in vistos:
            vistos.add(achado["video_id"])
            ids.append(achado["video_id"])

    if not ids:
        return {"erro": "Nenhuma faixa encontrada no YouTube Music.", "detalhes": detalhes}

    yt = _cliente(autenticado=True)
    resposta = yt.create_playlist(nome, descricao or "Criada pelo Bot de Playlists HaifaTools",
                                  privacy_status=privacidade, video_ids=ids)
    if not isinstance(resposta, str):
        return {"erro": f"O YouTube Music recusou a criação da playlist: {resposta}",
                "detalhes": detalhes}

    return {
        "plataforma": "YouTube Music",
        "link": f"https://music.youtube.com/playlist?list={resposta}",
        "adicionadas": len(ids),
        "nao_encontradas": sum(1 for d in detalhes if not d["resultado"]),
        "via_video_original": sum(1 for d in detalhes
                                  if d["resultado"] and d["resultado"]["origem"] == "video_original"),
        "detalhes": detalhes,
    }
