from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Playlists da HaifaTools está rodando com sucesso!"

@app.route('/processar', methods=['POST'])
def processar_playlist():
    dados = request.json
    link_youtube = dados.get('url')
    
    if not link_youtube:
        return jsonify({"erro": "Nenhum link enviado"}), 400
        
    try:
        # Extrai as músicas da playlist de origem do YouTube
        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
        }
        
        lista_musicas = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link_youtube, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    titulo = entry.get('title')
                    lista_musicas.append({
                        "titulo": titulo
                    })
            else:
                lista_musicas.append({
                    "titulo": info.get('title')
                })

        # Retorna a lista extraída (pronta para ser enviada ao YouTube Music)
        return jsonify({
            "status": "sucesso",
            "total_encontradas": len(lista_musicas),
            "musicas": lista_musicas,
            "mensagem": "Músicas extraídas com sucesso da playlist de origem!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
