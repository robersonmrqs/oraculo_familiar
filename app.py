# app.py

import os
import threading
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv

from src.oraculo_core import processar_pergunta
from src.ia_processor import inicializar_chroma, carregar_modelo_embedding, transcrever_audio_de_url

# Carrega as variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DA TWILIO ---
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

if not all([account_sid, auth_token, twilio_number]):
    print("ERRO CRÍTICO: As credenciais da Twilio não foram encontradas no arquivo .env")
    exit()

twilio_client = Client(account_sid, auth_token)

# --- CONFIGURAÇÃO DO FLASK E DO ORÁCULO ---
app = Flask(__name__)
historicos_de_conversa = {}

# Listas para uma conversa mais natural
SAUDACOES = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'e ai', 'eae', 'tudo bem', 'jarvis']
DESPEDIDAS = ['não', 'nao', 'nada', 'obrigado', 'obrigada', 'tchau', 'sair', 'fim', 'encerrar']

print("Inicializando componentes de IA no servidor...")
try:
    carregar_modelo_embedding()
    inicializar_chroma()
    print("Componentes de IA prontos para receber mensagens.")
except Exception as e:
    print(f"ERRO FATAL na inicialização dos modelos: {e}")

@app.route("/")
def hello_world():
    return "<h1>O servidor do Oráculo Familiar (Jarvis) está no ar!</h1>"

@app.route("/whatsapp", methods=['POST'])
def webhook_whatsapp():
    """
    Agora lida com mensagens de texto E de voz.
    """
    remetente = request.values.get('From', '')
    nome_usuario = request.values.get('ProfileName', 'Membro da Família')
    num_media = int(request.values.get('NumMedia', 0)) # Verifica se há mídia na mensagem

    mensagem_processada = ""

    # --- NOVA LÓGICA: TEXTO OU ÁUDIO? ---
    if num_media > 0:
        # É uma mensagem de áudio/mídia
        url_audio = request.values.get('MediaUrl0')
        print(f"Recebida mensagem de ÁUDIO de {nome_usuario} ({remetente})")
        texto_transcrito = transcrever_audio_de_url(url_audio)
        
        if not texto_transcrito:
            resposta_erro = "Desculpe, não consegui entender o áudio. Pode tentar novamente?"
            resposta_twilio = MessagingResponse()
            resposta_twilio.message(resposta_erro)
            return str(resposta_twilio)
        
        mensagem_processada = texto_transcrito
    else:
        # É uma mensagem de texto
        mensagem_processada = request.values.get('Body', '').strip()
        print(f"Mensagem de TEXTO recebida de {nome_usuario} ({remetente}): '{mensagem_processada}'")
    # --- FIM DA NOVA LÓGICA ---
    
    # Daqui para baixo, o fluxo é o mesmo, mas usando a "mensagem_processada"
    mensagem_lower_limpa = ''.join(c for c in mensagem_processada.lower() if c.isalnum() or c.isspace()).strip()
    palavras_da_mensagem = set(mensagem_lower_limpa.split())
    
    if any(saudacao in palavras_da_mensagem for saudacao in SAUDACOES):
        # ... (lógica de saudação permanece a mesma)
        resposta_texto = f"Olá, {nome_usuario}. Sou Jarvis. Em que posso ser útil?"
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(resposta_texto)
        return str(resposta_twilio)

    if len(palavras_da_mensagem) <= 3 and any(despedida in palavras_da_mensagem for despedida in DESPEDIDAS):
        # ... (lógica de despedida permanece a mesma)
        resposta_texto = "Entendido. Precisando, é só chamar! Até mais."
        if remetente in historicos_de_conversa: del historicos_de_conversa[remetente]
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(resposta_texto)
        return str(resposta_twilio)

    # Trata como uma pergunta para a IA
    thread = threading.Thread(
        target=processar_e_enviar_resposta,
        args=(remetente, mensagem_processada, nome_usuario),
        daemon=True
    )
    thread.start()

    resposta_imediata = MessagingResponse()
    resposta_imediata.message("Recebi sua mensagem... 🤔 Processando e já te envio a resposta!")
    return str(resposta_imediata)

def processar_e_enviar_resposta(remetente, mensagem_recebida, nome_usuario):
    """
    Roda em segundo plano, processa a pergunta e envia a resposta final.
    """
    print(f"Iniciando processamento em segundo plano para {nome_usuario}...")
    
    historico_usuario = historicos_de_conversa.get(remetente, [])
    resposta_do_oraculo = processar_pergunta(mensagem_recebida, historico_usuario)
    
    # Adiciona a pergunta de acompanhamento à resposta do LLM
    if "não encontrei informações" not in resposta_do_oraculo.lower():
        resposta_final = f"{resposta_do_oraculo}\n\nPosso ajudar em mais alguma coisa?"
    else:
        resposta_final = f"{resposta_do_oraculo}\nDeseja que eu tente buscar por outro termo?"

    # Atualiza o histórico
    historico_usuario.append({"role": "user", "content": mensagem_recebida})
    historico_usuario.append({"role": "assistant", "content": resposta_final})
    historicos_de_conversa[remetente] = historico_usuario

    try:
        print(f"Enviando resposta final para {nome_usuario}...")
        twilio_client.messages.create(
            from_=f"whatsapp:{twilio_number}",
            body=resposta_final,
            to=remetente
        )
        print("Resposta final enviada com sucesso.")
    except Exception as e:
        print(f"ERRO ao enviar mensagem final via API REST da Twilio: {e}")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)