# app.py

import os
import threading
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv

from src.oraculo_core import processar_pergunta
from src.ia_processor import inicializar_chroma, carregar_modelo_embedding

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
    remetente = request.values.get('From', '')
    mensagem_recebida = request.values.get('Body', '').strip()
    nome_usuario = request.values.get('ProfileName', 'Membro da Família')
    
    print(f"Mensagem recebida de {nome_usuario} ({remetente}): '{mensagem_recebida}'")

    mensagem_lower_limpa = ''.join(c for c in mensagem_recebida.lower() if c.isalnum() or c.isspace()).strip()
    
    # --- NOVA LÓGICA DE CONVERSA (SAUDAÇÃO E DESPEDIDA) ---
    palavras_da_mensagem = set(mensagem_lower_limpa.split())
    
    # 1. Verifica se é uma saudação
    if any(saudacao in palavras_da_mensagem for saudacao in SAUDACOES):
        resposta_texto = f"Olá, {nome_usuario}. Sou Jarvis, o Oráculo de sua família. Em que posso ser útil?"
        print(f"Enviando saudação de volta para {nome_usuario}.")
        
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(resposta_texto)
        return str(resposta_twilio)

    # 2. Verifica se é uma despedida
    # Consideramos uma despedida se for uma mensagem curta e contiver uma palavra de despedida
    if len(palavras_da_mensagem) <= 3 and any(despedida in palavras_da_mensagem for despedida in DESPEDIDAS):
        resposta_texto = "Entendido. Precisando, é só chamar! Até mais."
        # Limpa o histórico da conversa para um novo começo na próxima vez
        if remetente in historicos_de_conversa:
            del historicos_de_conversa[remetente]
        
        print(f"Encerrando a conversa com {nome_usuario}.")
        resposta_twilio = MessagingResponse()
        resposta_twilio.message(resposta_texto)
        return str(resposta_twilio)
    # --- FIM DA NOVA LÓGICA ---

    # Se não for saudação nem despedida, trata como uma pergunta para a IA
    thread = threading.Thread(
        target=processar_e_enviar_resposta,
        args=(remetente, mensagem_recebida, nome_usuario), # Passa o nome do usuário
        daemon=True
    )
    thread.start()

    resposta_imediata = MessagingResponse()
    resposta_imediata.message("Recebi sua pergunta... 🤔 Processando e já te envio a resposta!")

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