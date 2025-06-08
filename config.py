# config.py
"""
Arquivo de configuração centralizado para o projeto Oráculo Familiar.
Armazena todos os caminhos, nomes de modelos e parâmetros em um só lugar.
"""

# --- Configurações de Modelos de IA ---
MODELO_EMBEDDING = 'paraphrase-multilingual-MiniLM-L12-v2'
MODELO_LLM_OLLAMA = "llama3:instruct"
MODELO_WHISPER_STT = "small"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# --- Configurações de Banco de Dados ---
DB_NOME_ARQUIVO = "oraculo_familiar.db"
CHROMA_DATA_PATH = "chroma_db_store"
CHROMA_COLLECTION_NAME = "documentos_familiares"

# --- Configurações de Processamento ---
PASTA_DOCUMENTOS = "documentos_para_catalogar"
TAMANHO_CHUNK = 1000
SOBREPOSICAO_CHUNK = 150
TOP_N_CHUNKS = 5
LIMIAR_MINIMO_TEXTO_OCR = 100

# --- Configurações de Conversa ---
NOME_DO_BOT = "Jarvis"

# Lista de saudações aprimorada
SAUDACOES = [
    'oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'e ai', 
    'eae', 'tudo bem', NOME_DO_BOT.lower(), 'opa'
]

# Lista de despedidas aprimorada (com e sem acento)
DESPEDIDAS = [
    'não', 'nao', 'nada', 'obrigado', 'obrigada', 'tchau', 'sair', 
    'fim', 'encerrar', 'mais nada', 'só isso', 'so isso'
]

# Lista de stopwords aprimorada
STOPWORDS = [
    'a', 'o', 'e', 'de', 'do', 'da', 'para', 'com', 'um', 'uma', 'qual', 
    'quais', 'em', 'os', 'as', 'dos', 'das', 'é', 'foi', 'pela', 'pelo', 
    'são', 'me', 'diga', 'então', 'eu', 'quero', 'saber', 'pra', 'quem', 
    'ela', 'ele', 'mim', 'seu', 'sua'
]