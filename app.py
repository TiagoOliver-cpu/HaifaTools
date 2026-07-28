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
    
    # 1. Remove termos técnicos de gravação, câmeras e plataformas do meio do caminho
    titulo_limpo = re.sub(r'\b(keycam|live performance|clipe oficial|vídeo oficial|video oficial|ao vivo|dvd|medley|remix|ministração)\b', '', titulo_bruto, flags=re.IGNORECASE)
    
    # Remove parênteses e colchetes vazios ou residuais
    titulo_limpo = re.sub(r'[\(\[\{].*?[\)\]\}]', '', titulo_limpo)
    
    # 2. Divide os blocos por qualquer separador comum (- , – , |)
    partes = re.split(r'\s*[-–|]\s*', titulo_limpo)
    partes = [p.strip() for p in partes if p.strip()]
    
    if len(partes) >= 3:
        # Se tem muitos blocos (ex: "Tu És Deus + Sublime", "KeyCam", "Francesco Xavier")
        # O nome da música geralmente é o primeiro bloco
        musica = partes[0]
        # O artista real costuma estar no último bloco válido se o do meio for marca técnica
        artista = partes[-1]
    elif len(partes) == 2:
        # Verifica se o padrão veio invertido (Música | Artista ou Artista - Música)
        # Se a primeira parte tem características de música (frase longa/medley) e a segunda de artista
        p1, p2 = partes[0], partes[1]
        
        # Se contiver "+" ou parecer título de canção no primeiro bloco e nome no segundo
        if '+' in p1 or len(p1.split()) > 3:
            musica = p1
            artista = p2
        else:
            artista = p1
            musica = p2
    elif len(partes) == 1:
        musica = partes[0]
        artista = "Desconhecido"
    else:
        musica = titulo_bruto
        artista = "Desconhecido"
        
    return artista, musica

@app.route('/processar', methods=['POST'])
def processar_playlist():
    dados = request.json
    link_youtube = dados.get('url')
    
    if not link_youtube:
        return jsonify({"erro": "Nenhum link enviado"}), 400
        
    try:
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }
        
        lista_musicas = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link_youtube, download=False)
            
            entries = info.get('entries', [info])
            for entry in entries:
                if not entry:
                    continue
                titulo_bruto = entry.get('title')
                
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
            "mensagem": "Músicas extraídas ignorando marcas técnicas!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
