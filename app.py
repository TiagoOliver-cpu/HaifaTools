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
    
    # Remove termos comuns de vídeo/performance do final ou meio
    termo_limpeza = r'\b(clipe oficial|vídeo oficial|video oficial|ao vivo|live performance|live|dvd|medley|remix|ministração)\b'
    limpo = re.sub(r'[\(\[].*?' + termo_limpeza + r'.*?[\)\]]', '', titulo_bruto, flags=re.IGNORECASE)
    limpo = re.sub(termo_limpeza, '', limpo, flags=re.IGNORECASE)
    limpo = limpo.strip()
    
    # CASO 1: Se usa barra vertical "|" (ex: "Era Eu | Melk Villar")
    # O contexto padrão da barra vertical costuma ser: Música | Artista
    if '|' in limpo:
        partes = limpo.split('|')
        if len(partes) >= 2:
            musica = partes[0].strip()
            artista = partes[1].strip()
            return artista, musica

    # CASO 2: Se usa hífen ou travessão "-" (ex: "TU ÉS DEUS (A ELE) - O Canto das Igrejas, Paulo Cesar Baruk...")
    # O contexto padrão da indústria musical é: Música - Artista (ou projeto/intérpretes)
    if '-' in limpo or '–' in limpo:
        partes = re.split(r'\s*[-–]\s*', limpo)
        partes = [p.strip() for p in partes if p.strip()]
        
        if len(partes) >= 2:
            # O primeiro bloco é o nome da canção
            musica = partes[0]
            # Tudo o que vem depois do primeiro separador pertence ao contexto do(s) artista(s)/intérprete(s),
            # mesmo que seja longo ou tenha vários nomes (juntamos se houver mais divisões)
            artista = " - ".join(partes[1:])
            return artista, musica

    # Fallback se não encontrar nenhum separador
    return "Desconhecido", limpo

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
            "mensagem": "Músicas extraídas focando no contexto de intérpretes!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
