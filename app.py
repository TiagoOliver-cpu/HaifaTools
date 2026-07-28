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
    
    # Remove termos comuns de vídeo/performance do YouTube independentemente de estarem entre parênteses ou colchetes
    termo_limpeza = r'\b(clipe oficial|vídeo oficial|video oficial|ao vivo|live performance|live|dvd|medley|remix)\b'
    
    # Limpa parênteses e colchetes que contenham esses termos ou lixo comum
    limpo = re.sub(r'[\(\[].*?' + termo_limpeza + r'.*?[\)\]]', '', titulo_bruto, flags=re.IGNORECASE)
    # Remove também termos soltos no texto se sobram
    limpo = re.sub(termo_limpeza, '', limpo, flags=re.IGNORECASE)
    limpo = limpo.strip()
    
    # Tenta quebrar por separadores comuns (- ou |)
    partes = re.split(r'\s*[-–|]\s*', limpo)
    partes = [p.strip() for p in partes if p.strip()]
    
    if len(partes) >= 2:
        p1 = partes[0]
        p2 = partes[1]
        
        # Heurística de contexto:
        # Se o primeiro bloco for muito longo ou parecer um título de música/frase e o segundo for curto, inverte.
        # Nomes de artistas costumam ser curtos (até 3 ou 4 palavras).
        if len(p1.split()) > 4 and len(p2.split()) <= 4:
            musica = p1
            artista = p2
        else:
            # Padrão normal (Artista - Música)
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
