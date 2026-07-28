from flask import Flask, jsonify, request
import yt_dlp
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Playlists da HaifaTools está rodando com sucesso!"

def extrair_metadados(titulo_bruto, descricao_bruta):
    if not titulo_bruto:
        return "Desconhecido", "Desconhecido"
    
    artista = "Desconhecido"
    musica = ""

    # 1. Tenta buscar padrões explícitos dentro da DESCRIÇÃO do vídeo (onde geralmente estão os créditos oficiais)
    if descricao_bruta:
        # Procura por linhas como "Artista: X" ou "Cantor: X" ou "Música: Y"
        match_artista = re.search(r'(?:artista|cantor|interpret[eé]|voz):\s*([^\n]+)', descricao_bruta, re.IGNORECASE)
        match_musica = re.search(r'(?:música|faixa|canção|track):\s*([^\n]+)', descricao_bruta, re.IGNORECASE)
        
        if match_artista:
            artista = match_artista.group(1).strip()
        if match_musica:
            musica = match_musica.group(1).strip()

    # 2. Se não achou na descrição, recorre à inteligência de limpeza do TÍTULO
    if artista == "Desconhecido" or not musica:
        # Remove termos comuns de vídeo/performance do título
        termo_limpeza = r'\b(clipe oficial|vídeo oficial|video oficial|ao vivo|live performance|live|dvd|medley|remix|ministração)\b'
        limpo = re.sub(r'[\(\[].*?' + termo_limpeza + r'.*?[\)\]]', '', titulo_bruto, flags=re.IGNORECASE)
        limpo = re.sub(termo_limpeza, '', limpo, flags=re.IGNORECASE)
        limpo = limpo.strip()
        
        partes = re.split(r'\s*[-–|]\s*', limpo)
        partes = [p.strip() for p in partes if p.strip()]
        
        if len(partes) >= 2:
            p1 = partes[0]
            p2 = partes[1]
            
            # Se a primeira parte for longa e a segunda curta (ex: "Era Eu | Melk Villar"), inverte para achar o artista
            if len(p1.split()) > 2 and len(p2.split()) <= 3:
                musica = p1
                artista = p2
            else:
                artista = p1
                musica = p2
        elif len(partes) == 1:
            musica = partes[0]
        else:
            musica = titulo_bruto

    return artista, musica

@app.route('/processar', methods=['POST'])
def processar_playlist():
    dados = request.json
    link_youtube = dados.get('url')
    
    if not link_youtube:
        return jsonify({"erro": "Nenhum link enviado"}), 400
        
    try:
        # Configuração para extrair informações completas, incluindo descrição
        ydl_opts = {
            'extract_flat': False, # Mudado para False para garantir que traz detalhes como descrição se necessário, ou mantido leve
            'skip_download': True,
        }
        
        lista_musicas = []
        # Nota: para extrair a descrição de playlists grandes sem travar, usamos o extract_flat com cautela ou varremos os itens
        ydl_opts_flat = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info = ydl.extract_info(link_youtube, download=False)
            
            entries = info.get('entries', [info])
            for entry in entries:
                if not entry:
                    continue
                titulo_bruto = entry.get('title')
                # Tenta pegar a descrição se vier no pacote, senão busca o título limpo
                descricao_bruta = entry.get('description', '')
                
                artista, musica = extrair_metadados(titulo_bruto, descricao_bruta)
                
                lista_musicas.append({
                    "titulo_original": titulo_bruto,
                    "artista": artista,
                    "musica": musica
                })

        return jsonify({
            "status": "sucesso",
            "total_encontradas": len(lista_musicas),
            "musicas": lista_musicas,
            "mensagem": "Músicas extraídas analisando título e descrição!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
