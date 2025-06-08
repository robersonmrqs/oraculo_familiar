# src/ia_processor.py
"""
Módulo central para todas as operações de IA.
"""
import chromadb
import config
import os
import requests
import sqlite3
import tempfile
import whisper
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
from sentence_transformers import SentenceTransformer

# --- SETUP INICIAL ---
load_dotenv()
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

# Variáveis globais para armazenar os modelos carregados e evitar recarregamentos
model_embedding = None
model_whisper = None
chroma_client = None
chroma_collection = None


# --- FUNÇÕES DE INICIALIZAÇÃO E CARREGAMENTO DE MODELOS ---
def carregar_modelo_embedding():
    """Carrega o modelo de embedding sob demanda."""
    global model_embedding
    if model_embedding is None:
        print(f"Carregando modelo de embedding: {config.MODELO_EMBEDDING}...")
        model_embedding = SentenceTransformer(config.MODELO_EMBEDDING)
        print("Modelo de embedding carregado.")
    return model_embedding

def carregar_modelo_whisper():
    """Carrega o modelo Whisper para Speech-to-Text sob demanda."""
    global model_whisper
    if model_whisper is None:
        print(f"Carregando modelo Whisper STT: '{config.MODELO_WHISPER_STT}'...")
        model_whisper = whisper.load_model(config.MODELO_WHISPER_STT)
        print("Modelo Whisper carregado.")
    return model_whisper

def inicializar_chroma():
    """Inicializa o cliente ChromaDB e a coleção sob demanda."""
    global chroma_client, chroma_collection
    if chroma_client is None:
        print(f"Inicializando ChromaDB em: '{config.CHROMA_DATA_PATH}'")
        db_persist_path = Path(__file__).resolve().parent.parent / config.CHROMA_DATA_PATH
        chroma_client = chromadb.PersistentClient(path=str(db_persist_path))
    if chroma_collection is None:
        chroma_collection = chroma_client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        print(f"Coleção ChromaDB '{config.CHROMA_COLLECTION_NAME}' carregada/criada.")
    return chroma_collection

def inicializar_ia():
    """Função de conveniência para pré-carregar todos os modelos no início da aplicação."""
    print("Pré-inicializando todos os componentes de IA...")
    carregar_modelo_embedding()
    inicializar_chroma()
    # A chamada abaixo pode ser ativada se quisermos pré-carregar o whisper também
    # carregar_modelo_whisper() 
    print("Componentes de IA foram pré-inicializados com sucesso.")


# --- FUNÇÕES DE PROCESSAMENTO E INTERAÇÃO ---

def transcrever_audio_de_url(url_audio: str) -> str:
    """Baixa um arquivo de áudio de uma URL da Twilio e o transcreve para texto."""
    try:
        print(f"Baixando áudio da URL: {url_audio}")
        response = requests.get(url_audio, auth=(account_sid, auth_token))
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_audio_file:
            tmp_audio_file.write(response.content)
            tmp_audio_path = tmp_audio_file.name
        
        modelo_stt = carregar_modelo_whisper()
        resultado = modelo_stt.transcribe(tmp_audio_path, fp16=False)
        texto_transcrito = resultado.get('text', '').strip()
        print(f"Texto transcrito: '{texto_transcrito}'")

        os.remove(tmp_audio_path)
        return texto_transcrito
    except Exception as e:
        print(f"ERRO durante a transcrição do áudio: {e}")
        if 'tmp_audio_path' in locals() and os.path.exists(tmp_audio_path):
            os.remove(tmp_audio_path)
        return ""

def conectar_db():
    db_path = Path(__file__).resolve().parent.parent / config.DB_NOME_ARQUIVO
    return sqlite3.connect(db_path)

def obter_documentos_para_embedding():
    conn = conectar_db()
    cursor = conn.execute("SELECT id, nome_arquivo, texto_completo FROM documentos WHERE texto_completo IS NOT NULL AND texto_completo != '' AND indexado_no_chroma = 0")
    documentos = cursor.fetchall()
    conn.close()
    return documentos

def dividir_texto_em_chunks(texto: str) -> list[str]:
    if not texto: return []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.TAMANHO_CHUNK,
        chunk_overlap=config.SOBREPOSICAO_CHUNK,
        length_function=len
    )
    return text_splitter.split_text(texto)

def gerar_embeddings_para_chunks(chunks_de_texto: list[str]) -> list[list[float]]:
    modelo_carregado = carregar_modelo_embedding()
    if not chunks_de_texto: return []
    embeddings = modelo_carregado.encode(chunks_de_texto, convert_to_tensor=False)
    return embeddings.tolist()

def adicionar_chunks_ao_chroma(doc_id: int, nome_arquivo: str, chunks_texto: list[str], embeddings_vetores: list[list[float]]):
    collection = inicializar_chroma()
    if not all([collection, chunks_texto, embeddings_vetores]) or len(chunks_texto) != len(embeddings_vetores): return

    ids_chunks = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks_texto))]
    metadatas_chunks = [{"doc_id_original": doc_id, "nome_arquivo_original": nome_arquivo, "indice_chunk": i} for i in range(len(chunks_texto))]
    chunks_em_minusculas = [chunk.lower() for chunk in chunks_texto]
    try:
        collection.upsert(ids=ids_chunks, embeddings=embeddings_vetores, metadatas=metadatas_chunks, documents=chunks_em_minusculas)
        print(f"  - {len(ids_chunks)} chunks do doc ID {doc_id} ('{nome_arquivo}') adicionados/atualizados no ChromaDB.")
        # A responsabilidade de marcar como indexado foi movida para o script orquestrador.
    except Exception as e:
        print(f"Erro ao adicionar/atualizar chunks no ChromaDB para doc ID {doc_id}: {e}")

def buscar_chunks_relevantes(texto_pergunta: str, top_n: int) -> list[dict]:
    collection = inicializar_chroma()
    modelo_emb = carregar_modelo_embedding()
    if not all([texto_pergunta, collection, modelo_emb]): return []

    pergunta_lower = texto_pergunta.lower()
    palavras_da_pergunta = pergunta_lower.split()
    palavras_chave_dinamicas = [palavra.strip("?,.:;!") for palavra in palavras_da_pergunta if palavra.strip("?,.:;!") not in config.STOPWORDS]
    
    where_document_filter = None
    if palavras_chave_dinamicas:
        if len(palavras_chave_dinamicas) > 1:
            clausulas_filtro = [{"$contains": palavra} for palavra in palavras_chave_dinamicas]
            where_document_filter = {"$or": clausulas_filtro}
        elif len(palavras_chave_dinamicas) == 1:
            where_document_filter = {"$contains": palavras_chave_dinamicas[0]}

        if where_document_filter:
            print(f"  - Aplicando filtro de DOCUMENTO no ChromaDB: {where_document_filter}")
    else:
        print("  - Nenhuma palavra-chave específica identificada, fazendo busca semântica geral.")

    embedding_pergunta = modelo_emb.encode(texto_pergunta).tolist()
    
    try:
        resultados = collection.query(
            query_embeddings=[embedding_pergunta], n_results=top_n, where_document=where_document_filter, include=['documents', 'metadatas', 'distances']
        )
        chunks_encontrados = []
        if resultados and resultados.get('ids')[0]:
            for i in range(len(resultados['ids'][0])):
                chunks_encontrados.append({
                    "id_chunk_db": resultados['ids'][0][i], "texto_chunk": resultados['documents'][0][i],
                    "metadatos": resultados['metadatas'][0][i], "distancia": resultados['distances'][0][i]
                })
        return chunks_encontrados
    except Exception as e:
        print(f"Erro ao consultar o ChromaDB: {e}")
        return []

def gerar_resposta_com_llm(prompt: str, nome_modelo_llm: str) -> str:
    if not prompt.strip(): return "Erro: Prompt vazio."
    payload = {"model": nome_modelo_llm, "prompt": prompt, "stream": False}
    try:
        response = requests.post(config.OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        resposta_llm = response.json().get("response", "").strip()
        return resposta_llm
    except Exception as e:
        return f"Erro ao contatar o LLM: {e}"