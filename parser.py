"""Extração de artista/música a partir de títulos do YouTube.

Regras principais:
1. Remove "ruído" (ao vivo, clipe oficial, medley, nome de canal...) inclusive
   quando está dentro de parênteses, sem deixar "()" vazios para trás.
2. Divide o título em segmentos por "|" e por hífen com espaços ao redor
   (hífens dentro de palavras, como "Pré-Venda", são preservados).
3. Descarta segmentos que são só ruído ou descrição de álbum (DVD, CD, Álbum).
4. Decide quem é artista e quem é música usando pistas, em ordem de confiança:
   nome do canal > "+" (medley) > vírgula/&/feat > posição.
5. Devolve também uma lista de consultas candidatas (inclusive com artista e
   música trocados), porque a etapa de busca nas plataformas é quem confirma.
"""
import re

# Palavras/expressões que não fazem parte do nome da música nem do artista.
RUIDO = [
    "clipe oficial", "vídeo oficial", "video oficial", "videoclipe oficial",
    "áudio oficial", "audio oficial", "official video", "official audio",
    "official music video", "lyric video", "lyrics", "legendado", "letra",
    "live performance", "ministração", "ministracao", "ao vivo", "live",
    "medley", "remix", "cover", "keycam", "hd", "4k",
]
# Segmentos que começam assim descrevem o álbum/projeto, não a música.
PREFIXOS_ALBUM = ("dvd", "cd", "álbum", "album", "projeto")

_RUIDO_ALT = "|".join(sorted((re.escape(r) for r in RUIDO), key=len, reverse=True))
_RE_RUIDO = re.compile(rf"(?<!\w)(?:{_RUIDO_ALT})(?!\w)", re.IGNORECASE)
_RE_GRUPO = re.compile(r"[\(\[]([^\)\]]*)[\)\]]")
_RE_HIFEN = re.compile(r"\s+[-–—]\s+")
_RE_SO_PONTUACAO = re.compile(r"^[\W_]*$")


def _norm(texto):
    return re.sub(r"\s+", " ", texto or "").strip(" -–—|,.:;").strip()


_RE_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u200d\ufe0f]")


def _remover_ruido(texto):
    texto = _RE_EMOJI.sub("", texto)
    def grupo(m):
        interno = _RE_RUIDO.sub("", m.group(1))
        interno = _norm(interno)
        return f"({interno})" if interno else ""

    texto = _RE_GRUPO.sub(grupo, texto)   # parênteses/colchetes primeiro
    texto = _RE_RUIDO.sub("", texto)      # depois o ruído solto
    texto = re.sub(r"\(\s*\)", "", texto)
    return _norm(texto)


def _segmentos(titulo):
    """Retorna (lista de segmentos, usou_pipe)."""
    usou_pipe = "|" in titulo
    blocos = titulo.split("|")
    segmentos = []
    for bloco in blocos:
        for parte in _RE_HIFEN.split(bloco):
            parte = _norm(_remover_ruido(parte))
            if not parte or _RE_SO_PONTUACAO.match(parte):
                continue
            if parte.lower().startswith(PREFIXOS_ALBUM):
                continue
            segmentos.append(parte)
    return segmentos, usou_pipe


def _chave(texto):
    return re.sub(r"\W+", "", (texto or "").lower())


def _parece_artista(seg):
    s = seg.lower()
    return bool(re.search(r",|&| feat\.?| ft\.?| e | com ", s))


def _parece_musica(seg):
    return "+" in seg


def _limpar_titulo_base(titulo_bruto, canal=None):
    """Retorna dict: artista, musica, confianca ('alta'|'media'|'baixa'), candidatos."""
    if not titulo_bruto:
        return {"artista": "Desconhecido", "musica": "Desconhecido",
                "confianca": "baixa", "candidatos": []}

    segs, usou_pipe = _segmentos(titulo_bruto)

    if not segs:
        t = _norm(titulo_bruto)
        return {"artista": canal or "Desconhecido", "musica": t,
                "confianca": "baixa", "candidatos": [t]}

    if len(segs) == 1:
        return {"artista": canal or "Desconhecido", "musica": segs[0],
                "confianca": "baixa", "candidatos": [f"{segs[0]} {canal or ''}".strip(), segs[0]]}

    # Só os dois primeiros segmentos úteis: o resto costuma ser álbum/projeto.
    a, b = segs[0], segs[1]
    artista = musica = None
    confianca = "media"

    kc = _chave(canal)
    if kc and (kc in _chave(a) or _chave(a) in kc):
        artista, musica, confianca = a, b, "alta"
    elif kc and (kc in _chave(b) or _chave(b) in kc):
        artista, musica, confianca = b, a, "alta"
    elif _parece_musica(a) and not _parece_musica(b):
        musica, artista, confianca = a, b, "alta"
    elif _parece_musica(b) and not _parece_musica(a):
        musica, artista, confianca = b, a, "alta"
    elif _parece_artista(b) and not _parece_artista(a):
        musica, artista, confianca = a, b, "alta"
    elif _parece_artista(a) and not _parece_artista(b):
        artista, musica, confianca = a, b, "alta"
    elif usou_pipe:
        musica, artista = a, b            # "Música | Artista"
    else:
        artista, musica, confianca = a, b, "baixa"   # convenção "Artista - Música"

    candidatos = [f"{artista} {musica}", f"{musica} {artista}"]
    if confianca == "baixa":
        candidatos.append(musica)
    return {"artista": artista, "musica": musica,
            "confianca": confianca, "candidatos": candidatos}


def limpar_titulo(titulo_bruto, canal=None):
    """Igual ao base, mais a flag 'medley' (várias músicas num vídeo só)."""
    r = _limpar_titulo_base(titulo_bruto, canal)
    r["medley"] = bool(re.search(r"\+|\s/\s", r["musica"] or ""))
    return r
