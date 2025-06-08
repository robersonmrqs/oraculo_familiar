# app.py

from flask import Flask, request

# Cria a aplicação Flask
app = Flask(__name__)

# Define uma rota para a página inicial ("/")
# Acessível via método GET do navegador
@app.route("/")
def hello_world():
    # Retorna uma mensagem simples quando alguém acessa o endereço do servidor
    return "<h1>O servidor do Oráculo Familiar está no ar!</h1>"

# Define uma rota para o webhook do WhatsApp ("/whatsapp")
# Esta rota vai esperar por mensagens via método POST
@app.route("/whatsapp", methods=['POST'])
def webhook_whatsapp():
    # Por enquanto, vamos apenas pegar a mensagem recebida e imprimi-la no terminal
    mensagem_recebida = request.values.get('Body', '').lower()
    print(f"Mensagem recebida no webhook: '{mensagem_recebida}'")

    # E responder com uma mensagem padrão
    resposta = "Mensagem recebida pelo Oráculo!"
    return resposta

# Esta parte garante que o servidor só rode quando você executa "python app.py"
if __name__ == "__main__":
    # O host='0.0.0.0' torna o servidor acessível por qualquer IP da sua rede
    # O port=5000 é a porta padrão do Flask
    app.run(host='0.0.0.0', port=5000, debug=True)