# src/ia_processor.py

from sentence_transformers import SentenceTransformer
import sqlite3
from pathlib import Path
import chromadb
import requests
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- CONSTANTES DE CONFIGURAÇÃO ---
NOME_BANCO_DADOS = "oraculo_familiar.db"
MODELO_EMBEDDING = 'paraphrase-multilingual-MiniLM-L12-v2'
CHROMA_DATA_PATH = "chroma_db_store"
CHROMA_COLLECTION_NAME = "documentos_familiares"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Lista de palavras comuns a serem ignoradas na busca por filtro (stopwords)
STOPWORDS = [
    'a', 'o', 'e', 'de', 'do', 'da', 'para', 'com', 'um', 'uma', 'qual', 'quais',
    'em', 'os', 'as', 'dos', 'das', 'é', 'foi', 'pela', 'pelo', 'são'
]

# --- VARIÁVEIS GLOBAIS PARA OS CLIENTES (CARREGADOS SOB DEMANDA) ---
model = None
chroma_client = None
chroma_collection = None


def carregar_modelo_embedding():
    """Carrega o modelo de sentence transformer."""
    global model
    if model is None:
        print(f"Carregando o modelo de embedding: {MODELO_EMBEDDING}...")
        model = SentenceTransformer(MODELO_EMBEDDING)
        print("Modelo de embedding carregado.")
    return model

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    db_path = Path(__file__).resolve().parent.parent / NOME_BANCO_DADOS
    return sqlite3.connect(db_path)

def obter_documentos_para_embedding():
    """Busca documentos do banco de dados que possuem texto completo."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_arquivo, texto_completo FROM documentos WHERE texto_completo IS NOT NULL AND texto_completo != ''")
    documentos = cursor.fetchall()
    conn.close()
    return documentos

def dividir_texto_em_chunks(texto: str, tamanho_chunk: int = 1000, sobreposicao: int = 150) -> list[str]:
    """Divide um texto longo em chunks usando uma estratégia da biblioteca LangChain."""
    if not texto: return []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=tamanho_chunk, chunk_overlap=sobreposicao, length_function=len)
    return text_splitter.split_text(texto)

def gerar_embeddings_para_chunks(chunks_de_texto: list[str]) -> list[list[float]]:
    """Gera embeddings para uma lista de chunks de texto."""
    modelo_carregado = carregar_modelo_embedding()
    if not chunks_de_texto: return []
    print(f"Gerando embeddings para {len(chunks_de_texto)} chunks...")
    embeddings = modelo_carregado.encode(chunks_de_texto, convert_to_tensor=False)
    print("Embeddings gerados.")
    return embeddings.tolist()

def inicializar_chroma():
    """Inicializa o cliente ChromaDB e a coleção."""
    global chroma_client, chroma_collection
    if chroma_client is None:
        print(f"Inicializando ChromaDB com persistência em: '{CHROMA_DATA_PATH}'")
        db_persist_path = Path(__file__).resolve().parent.parent / CHROMA_DATA_PATH
        chroma_client = chromadb.PersistentClient(path=str(db_persist_path))
    if chroma_collection is None:
        try:
            chroma_collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
            print(f"Coleção ChromaDB '{CHROMA_COLLECTION_NAME}' carregada/criada.")
        except Exception as e:
            print(f"Erro ao obter/criar coleção ChromaDB: {e}")
            raise
    return chroma_collection

def adicionar_chunks_ao_chroma(doc_id: int, nome_arquivo: str, chunks_texto: list[str], embeddings_vetores: list[list[float]]):
    """Adiciona os chunks ao ChromaDB, convertendo o texto para MINÚSCULAS para busca case-insensitive."""
    collection = inicializar_chroma()
    if not all([collection, chunks_texto, embeddings_vetores]) or len(chunks_texto) != len(embeddings_vetores):
        print("Erro: Dados de entrada inválidos para adicionar ao ChromaDB.")
        return

    ids_chunks = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks_texto))]
    metadatas_chunks = [{"doc_id_original": doc_id, "nome_arquivo_original": nome_arquivo, "indice_chunk": i} for i in range(len(chunks_texto))]
    chunks_em_minusculas = [chunk.lower() for chunk in chunks_texto]

    try:
        collection.upsert(
            ids=ids_chunks,
            embeddings=embeddings_vetores,
            metadatas=metadatas_chunks,
            documents=chunks_em_minusculas
        )
        print(f"  - {len(ids_chunks)} chunks do doc ID {doc_id} ('{nome_arquivo}') adicionados/atualizados no ChromaDB.")
    except Exception as e:
        print(f"Erro ao adicionar/atualizar chunks no ChromaDB para doc ID {doc_id}: {e}")

def buscar_chunks_relevantes(texto_pergunta: str, top_n: int = 5) -> list[dict]:
    """Busca os chunks mais relevantes usando extração dinâmica de palavras-chave da pergunta."""
    modelo_emb = carregar_modelo_embedding()
    collection = inicializar_chroma()
    if not all([texto_pergunta, collection, modelo_emb]): return []

    print(f"\nBuscando chunks relevantes para a pergunta: '{texto_pergunta}'")
    
    pergunta_lower = texto_pergunta.lower()
    palavras_da_pergunta = pergunta_lower.split()
    palavras_chave_dinamicas = [palavra.strip("?,.:;!") for palavra in palavras_da_pergunta if palavra.strip("?,.:;!") not in STOPWORDS]
    
    where_document_filter = None
    if palavras_chave_dinamicas:
        print(f"  - Palavras-chave dinâmicas identificadas: {palavras_chave_dinamicas}")
        
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
            query_embeddings=[embedding_pergunta],
            n_results=top_n,
            where_document=where_document_filter,
            include=['documents', 'metadatas', 'distances']
        )
        
        chunks_encontrados = []
        if resultados and resultados.get('ids')[0]:
            print(f"  - Encontrados {len(resultados['ids'][0])} chunks candidatos.")
            for i in range(len(resultados['ids'][0])):
                chunks_encontrados.append({
                    "id_chunk_db": resultados['ids'][0][i],
                    "texto_chunk": resultados['documents'][0][i],
                    "metadados": resultados['metadatas'][0][i],
                    "distancia": resultados['distances'][0][i]
                })
        return chunks_encontrados
    except Exception as e:
        print(f"Erro ao consultar o ChromaDB: {e}")
        return []

def gerar_resposta_com_llm(prompt: str, nome_modelo_llm: str) -> str:
    """Envia um prompt para o LLM via API do Ollama e retorna a resposta."""
    if not prompt.strip(): return "Erro: Prompt vazio."
    print(f"\nEnviando prompt para o LLM ({nome_modelo_llm})...")
    payload = {"model": nome_modelo_llm, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        resposta_llm = response_data.get("response", "").strip()
        print("Resposta recebida do LLM.")
        return resposta_llm
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão/comunicação com a API do Ollama: {e}")
        return f"Erro ao contatar o LLM. Verifique se o Ollama está rodando e o modelo '{nome_modelo_llm}' está disponível. Erro: {e}"
    except Exception as e:
        print(f"Erro inesperado ao interagir com o LLM: {e}")
        return f"Erro inesperado com LLM: {e}"