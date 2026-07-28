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
        # Configuração do yt-dlp para extrair apenas os dados da playlist sem baixar vídeos
        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
        }
        
        lista_musicas = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link_youtube, download=False)
            
            # Se for uma playlist, percorre os itens
            if 'entries' in info:
                for entry in info['entries']:
                    titulo = entry.get('title')
                    lista_musicas.append({
                        "titulo": titulo
                    })
            else:
                # Se for apenas um vídeo solto
                lista_musicas.append({
                    "titulo": info.get('title')
                })

        return jsonify({
            "status": "sucesso",
            "total_encontradas": len(lista_musicas),
            "musicas": lista_musicas
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
