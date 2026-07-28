from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Playlists da HaifaTools está rodando com sucesso!"

@app.route('/processar', methods=['POST'])
def processar_playlist():
    # Aqui é onde o bot vai receber o link do YouTube futuramente
    dados = request.json
    link_youtube = dados.get('url')
    
    if not link_youtube:
        return jsonify({"erro": "Nenhum link enviado"}), 400
        
    # Resposta simulada por enquanto
    return jsonify({
        "status": "sucesso",
        "mensagem": f"Link recebido com sucesso: {link_youtube}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
