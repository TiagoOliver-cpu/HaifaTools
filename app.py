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
    
    # 1. Remove termos técnicos e de gravação do final do texto
    titulo_limpo = re.sub(r'\b(keycam|live performance|clipe oficial|vídeo oficial|video oficial|ao vivo|dvd|medley|remix|ministração)\b', '', titulo_bruto, flags=re.IGNORECASE)
    titulo_limpo = titulo_limpo.strip()
    
    # 2. Identifica o separador principal que divide a Música e o Artista.
    # No caso de "TU ÉS DEUS (A ELE) - O Canto das Igrejas...", queremos que o hífen principal 
    # seja o que separa o nome da música (incluindo o (A ELE)) do grupo de artistas.
    # Vamos procurar o primeiro hífen ou travessão que vem DEPOIS de parênteses, se houver.
    
    # Se tem barra vertical "|", o padrão costuma ser Música | Artista
    if '|' in titulo_limpo:
        partes = titulo_limpo.split('|')
        musica = partes[0].strip()
        artista = partes[1].strip() if len(partes) > 1 else "Desconhecido"
        return artista, musica

    # Para hífens/travessões (-)
    # Procuramos o split de forma inteligente: se o título tem parênteses, o artista geralmente vem após o último hífen principal
    if '-' in titulo_limpo or '–' in titulo_limpo:
        # Divide mantendo o contexto
        partes = re.split(r'\s*[-–]\s*', titulo_limpo)
        partes = [p.strip() for p in partes if p.strip()]
        
        if len(partes) >= 2:
            # Se a primeira parte tem parênteses abertos e fechados logo no começo, ou se é o título principal
            # Vamos juntar as partes iniciais caso o título tenha sido cortado por um hífen interno (ex: "TU ÉS DEUS (A ELE)")
            if '(' in partes[0] and ')' not in partes[0] and len(partes) >= 3:
                musica = f"{partes[0]} - {partes[1]}"
                artista = " - ".join(partes[2:])
            else:
                musica = partes[0]
                artista = " - ".join(partes[1:])
            return artista, musica

    return "Desconhecido", titulo_limpo

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
            "mensagem": "Músicas extraídas com correção de hífens internos!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
