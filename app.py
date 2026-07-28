from flask import Flask, jsonify, request
import yt_dlp
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Playlists da HaifaTools está rodando com sucesso!"

def limpar_titulo(titulo_bruto):
    if not titulo_bruto:
        return "Desconhecido", "Desconhecido"
    
    # Tenta separar por hífen comum ou travessão (-)
    partes = re.split(r'\s*[-–]\s*', titulo_bruto, maxsplit=1)
    
    if len(partes) == 2:
        artista = partes[0].strip()
        musica = partes[1].strip()
    else:
        artista = "Desconhecido"
        musica = titulo_bruto.strip()
        
    # Remove sujeiras comuns do YouTube do título da música (ex: (Clipe Oficial), [Ao Vivo], etc)
    musica = re.sub(r'\(.*?(oficial|live|ao vivo|clipe|video).*?\)', '', musica, flags=re.IGNORECASE)
    musica = re.sub(r'\[.*?(oficial|live|ao vivo|clipe|video).*?\]', '', musica, flags=re.IGNORECASE)
    musica = musica.strip()
    
    return artista, musica

@app.route('/processar', methods=['POST'])
def processar_playlist():
    dados = request.json
    link_youtube = dados.get('url')
    
    if not link_youtube:
        return jsonify({"erro": "Nenhum link enviado"}), 400
        
    try:
        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
        }
        
        lista_musicas = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link_youtube, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    titulo_bruto = entry.get('title')
                    artista, musica = limpar_titulo(titulo_bruto)
                    
                    lista_musicas.append({
                        "titulo_original": titulo_bruto,
                        "artista": artista,
                        "musica": musica
                    })
            else:
                titulo_bruto = info.get('title')
                artista, musica = limpar_titulo(titulo_bruto)
                lista_musicas.append({
                    "titulo_original": titulo_bruto,
                    "artista": artista,
                    "musica": musica
                })

        return jsonify({
            "status": "sucesso",
            "total_encontradas": len(lista_musicas),
            "musicas": lista_musicas,
            "mensagem": "Músicas extraídas e limpas com sucesso!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
