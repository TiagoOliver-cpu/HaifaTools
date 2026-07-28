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
    
    # 1. Remove termos universais de vídeo/performance independentemente de onde estejam
    termo_limpeza = r'\b(clipe oficial|vídeo oficial|video oficial|ao vivo|live performance|live|dvd|medley|remix|ministração)\b'
    
    limpo = re.sub(r'[\(\[].*?' + termo_limpeza + r'.*?[\)\]]', '', titulo_bruto, flags=re.IGNORECASE)
    limpo = re.sub(termo_limpeza, '', limpo, flags=re.IGNORECASE)
    limpo = limpo.strip()
    
    # 2. Quebra o título nos separadores comuns (- ou |)
    partes = re.split(r'\s*[-–|]\s*', limpo)
    partes = [p.strip() for p in partes if p.strip()]
    
    if len(partes) >= 2:
        p1 = partes[0]
        p2 = partes[1]
        
        # Heurística de Nomes Próprios e Contexto:
        # Se a segunda parte parece mais um nome próprio/artista (geralmente até 3 palavras, iniciais maiúsculas, sem verbos de frase comum)
        # Exemplo: "Era Eu | Melk Villar" -> p2 é "Melk Villar", logo é o artista.
        # Vamos verificar se p2 tem cara de artista e p1 tem cara de música (frase/título).
        
        # Indicadores simples de que o texto é um nome (poucas palavras, sem termos longos)
        palavras_p2 = p2.split()
        palavras_p1 = p1.split()
        
        # Se p1 é longo (frase de música) e p2 é curto (nome do cantor)
        if len(palavras_p1) > 2 and len(palavras_p2) <= 3:
            musica = p1
            artista = p2
        elif len(palavras_p2) > 2 and len(palavras_p1) <= 3:
            # Caso contrário, se o p1 for o artista curto ("Aline Barros - Casa do Pai")
            artista = p1
            musica = p2
        else:
            # Padrão padrão caso ambos tenham tamanhos parecidos
            artista = p1
            musica = p2
            
        # Se houver uma terceira parte e ela for curta (ex: participações ou bandas no fim)
        if len(partes) > 2 and len(partes[-1].split()) <= 3:
            # Se a última parte parecer um artista válido, podemos somar ou considerar
            pass
            
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
            "mensagem": "Músicas extraídas com reconhecimento de nomes!"
        })
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
