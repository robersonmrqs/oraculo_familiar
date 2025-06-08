# app.py
"""
Servidor Flask que atua como webhook para o WhatsApp, usando a classe Oraculo.
"""
import config
import os
import threading
from dotenv import load_dotenv
from flask import Flask, request
from src.ia_processor import inicializar_ia, transcrever_audio_de_url
from src.jarvis import Oraculo
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

# --- Configurações e Clientes ---
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

if not all([account_sid, auth_token, twilio_number]):
    print("ERRO CRÍTICO: Credenciais da Twilio não configuradas no arquivo .env")
    exit()

twilio_client = Client(account_sid, auth_token)
app = Flask(__name__)

# Dicionário para armazenar uma instância do Oraculo para cada usuário (número de telefone)
sessoes_de_conversa = {}

# --- Inicialização ---
try:
    inicializar_ia()
except Exception as e:
    print(f"ERRO FATAL na inicialização dos componentes de IA: {e}")

# --- Lógica do Servidor ---
def processar_e_enviar_resposta(remetente, mensagem_recebida):
    """Obtém a instância do Oraculo para o usuário e processa a pergunta."""
    jarvis = sessoes_de_conversa.get(remetente)
    if not jarvis:
        print(f"AVISO: Nenhuma sessão encontrada para {remetente}, mas a pergunta foi processada sem histórico.")
        jarvis = Oraculo(remetente) # Cria uma sessão temporária
    
    resposta_final = jarvis.obter_resposta(mensagem_recebida)
    # Adiciona a pergunta de acompanhamento
    if "não encontrei informações" not in resposta_final.lower():
        resposta_final += f"\n\nPosso ajudar em mais alguma coisa, {jarvis.nome_usuario}?"
    
    try:
        twilio_client.messages.create(
            from_=f"whatsapp:{twilio_number}", body=resposta_final, to=remetente
        )
        print(f"Resposta final enviada com sucesso para {remetente}.")
    except Exception as e:
        print(f"ERRO ao enviar mensagem final via API REST da Twilio: {e}")

@app.route("/whatsapp", methods=['POST'])
def webhook_whatsapp():
    """Recebe mensagens do WhatsApp, lida com saudações/despedidas e dispara a IA."""
    remetente = request.values.get('From', '')
    nome_usuario = request.values.get('ProfileName', remetente)
    num_media = int(request.values.get('NumMedia', 0))
    mensagem_recebida = ""

    if num_media > 0:
        url_audio = request.values.get('MediaUrl0')
        mensagem_recebida = transcrever_audio_de_url(url_audio)
    else:
        mensagem_recebida = request.values.get('Body', '').strip()

    if not mensagem_recebida: # Se a transcrição falhar ou a mensagem for vazia
        return ""

    # Garante que uma sessão exista para o usuário
    if remetente not in sessoes_de_conversa:
        sessoes_de_conversa[remetente] = Oraculo(nome_usuario=nome_usuario)
    
    jarvis_instance = sessoes_de_conversa[remetente]

    palavras_da_mensagem = set(mensagem_recebida.lower().split())

    # Lógica de Saudação e Despedida
    if any(saudacao in palavras_da_mensagem for saudacao in config.SAUDACOES):
        resposta_texto = f"Olá, {jarvis_instance.nome_usuario}. Sou {config.NOME_DO_BOT}, à sua disposição."
        resp = MessagingResponse()
        resp.message(resposta_texto)
        return str(resp)

    if len(palavras_da_mensagem) <= 3 and any(despedida in palavras_da_mensagem for despedida in config.DESPEDIDAS):
        resposta_texto = "Entendido. Precisando, é só chamar!"
        del sessoes_de_conversa[remetente] # Encerra a sessão
        resp = MessagingResponse()
        resp.message(resposta_texto)
        return str(resp)

    # Dispara a IA em uma thread
    thread = threading.Thread(target=processar_e_enviar_resposta, args=(remetente, mensagem_recebida))
    thread.start()

    # Responde imediatamente
    resp_imediata = MessagingResponse()
    resp_imediata.message("Recebi sua mensagem. Processando...")
    return str(resp_imediata)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)