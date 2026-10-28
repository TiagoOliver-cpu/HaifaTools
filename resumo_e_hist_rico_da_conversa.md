# Histórico de Desenvolvimento: Bot de Playlists HaifaTools

Este documento registra o progresso, testes, diagnósticos e otimizações realizadas durante o desenvolvimento da API de extração de metadados do bot de playlists.

---

## 1. Resolução do Erro Inicial de Conexão (Hoppscotch)

### Problema:
Durante as requisições enviadas ao endpoint `https://haifa-tools-bot.onrender.com/processar` pelo Hoppscotch, ocorria o erro:
`Network Error: Unknown cause`

### Causa e Solução:
1. **Bloqueio de CORS / Origem pelo Navegador:** Solucionado ao alternar o **Interceptor** do Hoppscotch para o modo **Proxy** ou utilizar a **Extensão do Hoppscotch** com origens liberadas.
2. **Servidor em Modo Sleep (Render):** O plano gratuito do Render desativa instâncias inativas. Foi necessário fazer o "warm-up" acessando a rota raiz (`/`) antes de disparar o `POST`.

---

## 2. Evolução da Lógica de Limpeza e Separação de Metadados (`app.py`)

O objetivo principal das alterações foi separar corretamente o **Nome do Artista/Intérprete** do **Título da Canção**, considerando a enorme variação de formatos utilizados no YouTube.

### Casos de Teste Analisados:
* `Santo + Oh Quão Lindo esse Nome é - Jadson Moreno - Ministração Ao Vivo`
* `Era Eu | Melk Villar (Clipe Oficial)`
* `TU ÉS DEUS (A ELE) - O Canto das Igrejas, Paulo Cesar Baruk, Lucas & Evelyn Cortazio`
* `Aline Barros - Casa do Pai (Ao Vivo) - DVD Extraordinária Graça`
* `Tu És Deus + Sublime (Medley) | Live Performance - KeyCam | Francesco Xavier`

---

## 3. Estado Atual do Código (`app.py`)

Abaixo está a versão mais recente implementada no repositório GitHub e hospedada no Render, com a lógica de tratamento de hífens internos, parênteses e separadores `|`:

```python
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
    if '|' in titulo_limpo:
        partes = titulo_limpo.split('|')
        musica = partes[0].strip()
        artista = partes[1].strip() if len(partes) > 1 else "Desconhecido"
        return artista, musica

    # Para hífens/travessões (-)
    if '-' in titulo_limpo or '–' in titulo_limpo:
        partes = re.split(r'\s*[-–]\s*', titulo_limpo)
        partes = [p.strip() for p in partes if p.strip()]
        
        if len(partes) >= 2:
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
```

---

## 4. Próximos Passos Combinados

* **Validação Exata na Fase de Criação da Playlist:** Em vez de depender 100% de heurísticas em strings puras durante a extração, a identificação do artista original/oficial será refinada na etapa seguinte de busca direta na API do YouTube Music (cruzando `musica` e `artista`).