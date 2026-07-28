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
    
    # Remove termos comuns de vídeo/performance
    termo_limpeza = r'\b(clipe oficial|vídeo oficial|video oficial|ao vivo|live performance|live|dvd|medley|remix|ministração)\b'
    limpo = re.sub(r'[\(\[].*?' + termo_limpeza + r'.*?[\)\]]', '', titulo_bruto, flags=re.IGNORECASE)
    limpo = re.sub(termo_limpeza, '', limpo, flags=re.IGNORECASE)
    limpo = limpo.strip()
    
    # CASO ESPECIAL: Se o título usa barra vertical "|", o padrão comum é "Música | Artista" (ex: Era Eu | Melk Villar)
    if '|' in limpo:
        partes = limpo.split('|')
        if len(partes) >= 2:
            musica = partes[0].strip()
            artista = partes[1].strip()
            return artista, musica

    # Padrão normal com hífen (-)
    partes = re.split(r'\s*[-–]\s*', limpo)
    partes = [p.strip() for p in partes if p.strip()]
    
    if len(partes) >= 2:
        p1 = partes[0]
        p2 = partes[1]
        
        # Se a primeira parte for longa e a segunda curta, inverte
        if len(p1.split()) > 2 and len(p2.split()) <= 3:
            musica = p1
            artista = p2
        else:
            artista = p1
            musica = p2
    elif len(partes) == 1:
        artista = "Desconhecido"
        musica = partes[0]
    else:
        artista = "Desconhecido"
        musica = titulo_bruto
        
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
            "mensagem": "Músicas extraídas com ajuste para separador de barra!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
