import os

import yt_dlp
from flask import Flask, jsonify, request
from flask_cors import CORS

from parser import limpar_titulo
from ytmusic import criar_playlist_ytmusic

app = Flask(__name__)
CORS(app)  # libera chamadas vindas do navegador (Hoppscotch, front-end futuro)

TITULOS_INVALIDOS = {"[private video]", "[deleted video]"}


@app.route("/")
@app.route("/health")
def home():
    return "Bot de Playlists da HaifaTools está rodando com sucesso!"


def extrair_playlist(url):
    opcoes = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("Não foi possível ler esse link do YouTube.")

    entradas = info.get("entries") or [info]
    musicas = []
    for entrada in entradas:
        if not entrada:
            continue
        titulo = entrada.get("title")
        if not titulo or titulo.strip().lower() in TITULOS_INVALIDOS:
            continue
        canal = entrada.get("channel") or entrada.get("uploader")
        if canal:
            canal = canal.replace(" - Topic", "").strip()
        dados = limpar_titulo(titulo, canal)
        musicas.append({
            "titulo_original": titulo,
            "canal": canal,
            "duracao_s": entrada.get("duration"),
            "video_id": entrada.get("id"),
            **dados,
        })
    nome = " ".join((info.get("title") or "").split()) or None
    return nome, musicas


@app.route("/processar", methods=["POST"])
def processar_playlist():
    dados = request.get_json(silent=True) or {}
    link = (dados.get("url") or "").strip()
    if not link:
        return jsonify({"erro": "Nenhum link enviado. Envie JSON no formato {\"url\": \"...\"}"}), 400

    try:
        nome, musicas = extrair_playlist(link)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    revisar = [m["titulo_original"] for m in musicas if m["confianca"] == "baixa"]
    resposta = {
        "status": "sucesso",
        "nome_playlist": nome,
        "total_encontradas": len(musicas),
        "para_revisar": revisar,
        "musicas": musicas,
    }

    # Opcional: {"criar_ytmusic": true, "privacidade": "UNLISTED"|"PUBLIC"|"PRIVATE"}
    if dados.get("criar_ytmusic"):
        privacidade = str(dados.get("privacidade", "UNLISTED")).upper()
        if privacidade not in {"PUBLIC", "PRIVATE", "UNLISTED"}:
            privacidade = "UNLISTED"
        try:
            resposta["ytmusic"] = criar_playlist_ytmusic(
                musicas, dados.get("nome") or nome or "Playlist HaifaTools",
                privacidade=privacidade)
        except Exception as e:
            resposta["ytmusic"] = {"erro": str(e)}

    return jsonify(resposta)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
