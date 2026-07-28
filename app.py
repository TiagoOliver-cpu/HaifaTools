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
    
    # Remove sujeiras comuns do YouTube do título inteiro primeiro
    limpo = re.sub(r'\(.*?(oficial|live|ao vivo|clipe|video|performance|medley|dvd).*?\)', '', titulo_bruto, flags=re.IGNORECASE)
    limpo = re.sub(r'\[.*?(oficial|live|ao vivo|clipe|video|performance|medley|dvd).*?\]', '', limpo, flags=re.IGNORECASE)
    limpo = limpo.strip()
    
    # Tenta quebrar por separadores comuns (- ou |)
    partes = re.split(r'\s*[-–|]\s*', limpo)
    
    if len(partes) >= 2:
        # Analisa os pedaços para tentar deduzir o contexto
        # Normalmente o artista é o nome mais curto ou o que aparece isolado
        # Vamos assumir uma regra inteligente padrão: parte 1 = Artista / parte 2 = Música (ou vice-versa dependendo do tamanho)
        p1 = partes[0].strip()
        p2 = partes[1].strip()
        
        # Se a primeira parte for muito longa (ex: nome de medley grande), inverte ou trata
        if len(p1) > 30 and len(p2) < 30:
            artista = p2
            musica = p1
        else:
            artista = p1
            musica = p2
    else:
        artista = "Desconhecido"
        musica = limpo
        
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
            "mensagem": "Músicas extraídas com análise de contexto!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
