# src/ia_processor.py
import chromadb
import json
import requests
import sqlite3
from pathlib import Path
from sentence_transformers import SentenceTransformer

NOME_BANCO_DADOS = "oraculo_familiar.db"

MODELO_EMBEDDING = 'paraphrase-multilingual-MiniLM-L12-v2'
model = None # Vamos carregar o modelo sob demanda

# --- Configurações do ChromaDB ---
CHROMA_DATA_PATH = "chroma_db_store" # Pasta onde o ChromaDB salvará os dados
CHROMA_COLLECTION_NAME = "documentos_familiares"
chroma_client = None
chroma_collection = None

def carregar_modelo_embedding():
    """Carrega o modelo de sentence transformer."""
    global model
    if model is None:
        print(f"Carregando o modelo de embedding: {MODELO_EMBEDDING}...")
        model = SentenceTransformer(MODELO_EMBEDDING)
        print("Modelo carregado.")
    return model

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    # Adaptado de database_manager.py para simplicidade aqui
    # Idealmente, teríamos um local central para a configuração do DB Path
    db_path = Path(__file__).resolve().parent.parent / NOME_BANCO_DADOS
    return sqlite3.connect(db_path)

def obter_documentos_para_embedding():
    """Busca documentos do banco de dados que possuem texto completo."""
    conn = conectar_db()
    cursor = conn.cursor()
    # Vamos pegar id, nome_arquivo e texto_completo
    # Poderíamos adicionar um campo 'embeddings_gerados BOOLEAN' no futuro
    # para processar apenas documentos novos/atualizados.
    cursor.execute("SELECT id, nome_arquivo, texto_completo FROM documentos WHERE texto_completo IS NOT NULL AND texto_completo != ''")
    documentos = cursor.fetchall()
    conn.close()
    return documentos # Lista de tuplas: (id, nome_arquivo, texto_completo)

# --- Função de Chunking (Divisão de Texto) ---
# Vamos implementar uma estratégia simples de chunking primeiro.
# Poderíamos usar NLTK para sentenças, ou LangChain/LlamaIndex para splitters mais avançados.

def dividir_texto_em_chunks(texto: str, tamanho_chunk: int = 500, sobreposicao: int = 50) -> list[str]:
    """
    Divide um texto longo em chunks menores com alguma sobreposição.
    tamanho_chunk: número aproximado de caracteres por chunk.
    sobreposicao: número de caracteres que se sobrepõem entre chunks consecutivos.
    """
    if not texto:
        return []

    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = min(inicio + tamanho_chunk, len(texto))
        chunks.append(texto[inicio:fim])
        if fim == len(texto):
            break
        inicio += (tamanho_chunk - sobreposicao)
        if inicio >= len(texto): # Evitar loop infinito se sobreposicao for muito grande
            break
    return chunks

# --- Função de Geração de Embeddings ---
def gerar_embeddings_para_chunks(chunks_de_texto: list[str]) -> list[list[float]]:
    """Gera embeddings para uma lista de chunks de texto."""
    modelo_carregado = carregar_modelo_embedding()
    if not chunks_de_texto:
        return []

    print(f"Gerando embeddings para {len(chunks_de_texto)} chunks...")
    embeddings = modelo_carregado.encode(chunks_de_texto, convert_to_tensor=False)
    # convert_to_tensor=False retorna numpy arrays, que são mais fáceis de serializar/armazenar
    # do que tensores PyTorch, se formos salvar em JSON ou algo similar antes do Vector DB.
    print("Embeddings gerados.")
    return embeddings.tolist() # Converte numpy arrays para listas de floats

def inicializar_chroma():
    """Inicializa o cliente ChromaDB e a coleção."""
    global chroma_client, chroma_collection
    
    if chroma_client is None:
        print(f"Inicializando ChromaDB com persistência em: '{CHROMA_DATA_PATH}'")
        # Usar PersistentClient para salvar os dados em disco
        # A pasta será criada na raiz do projeto se não existir
        db_persist_path = Path(__file__).resolve().parent.parent / CHROMA_DATA_PATH
        chroma_client = chromadb.PersistentClient(path=str(db_persist_path))
    
    if chroma_collection is None:
        try:
            # Tenta obter a coleção. Se não existir, cria.
            # Usamos 'cosine' como métrica de distância, comum para embeddings de texto.
            chroma_collection = chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"} 
            )
            print(f"Coleção ChromaDB '{CHROMA_COLLECTION_NAME}' carregada/criada.")
        except Exception as e:
            print(f"Erro ao obter/criar coleção ChromaDB: {e}")
            # Em caso de erro grave aqui, talvez relançar ou tratar de forma mais robusta.
            # Por exemplo, se o banco de dados estiver corrompido.
            # Para desenvolvimento, apagar a pasta CHROMA_DATA_PATH pode resolver.
            raise 
            
    return chroma_collection

def adicionar_chunks_ao_chroma(doc_id: int, nome_arquivo: str, chunks_texto: list[str], embeddings_vetores: list[list[float]]):
    """
    Adiciona os chunks de texto e seus embeddings a uma coleção no ChromaDB.
    Usa 'upsert' para adicionar novos ou atualizar existentes.
    """
    collection = inicializar_chroma()
    if not collection:
        print("Erro: Coleção ChromaDB não inicializada. Não é possível adicionar chunks.")
        return

    if not chunks_texto or not embeddings_vetores or len(chunks_texto) != len(embeddings_vetores):
        print("Erro: Listas de chunks ou embeddings vazias ou com tamanhos diferentes.")
        return

    # Preparar os dados para o ChromaDB
    ids_chunks = []       # IDs únicos para cada chunk
    metadatas_chunks = [] # Metadados para cada chunk
    
    for i, texto_do_chunk in enumerate(chunks_texto):
        chunk_id_unico = f"doc{doc_id}_chunk{i}" # Cria um ID único para o chunk
        ids_chunks.append(chunk_id_unico)
        metadatas_chunks.append({
            "doc_id_original": doc_id,
            "nome_arquivo_original": nome_arquivo,
            "indice_chunk": i,
            # "texto_preview_chunk": texto_do_chunk[:100] + "..." # O Chroma armazena o documento (chunk) inteiro
        })

    try:
        # Usar collection.upsert() é mais robusto para execuções repetidas.
        # Ele adiciona se o ID não existir, ou atualiza se o ID já existir.
        collection.upsert(
            ids=ids_chunks,
            embeddings=embeddings_vetores,
            metadatas=metadatas_chunks,
            documents=chunks_texto # O ChromaDB pode armazenar o texto do chunk diretamente
        )
        print(f"  - {len(ids_chunks)} chunks do doc ID {doc_id} ('{nome_arquivo}') adicionados/atualizados no ChromaDB.")
    except Exception as e:
        print(f"Erro ao adicionar/atualizar chunks no ChromaDB para doc ID {doc_id}: {e}")

def buscar_chunks_relevantes(texto_pergunta: str, top_n: int = 5, limiar_distancia: float = 0.6) -> list[dict]: # <<< PARÂMETROS AJUSTADOS
    """
    Busca os chunks de texto mais relevantes para uma pergunta no ChromaDB.
    
    Args:
        texto_pergunta: A pergunta do usuário.
        top_n: O número de chunks a serem inicialmente recuperados.
        limiar_distancia: A distância máxima para um chunk ser considerado relevante.
        
    Returns:
        Uma lista de dicionários com os chunks relevantes que passaram no filtro.
    """
    modelo_emb = carregar_modelo_embedding()
    collection = inicializar_chroma()

    if not texto_pergunta or not collection or not modelo_emb:
        print("Erro: Pergunta vazia, coleção Chroma não inicializada ou modelo de embedding não carregado.")
        return []

    print(f"\nBuscando chunks relevantes para a pergunta: '{texto_pergunta}'")
    
    embedding_pergunta = modelo_emb.encode(texto_pergunta).tolist()
    
    try:
        # Aumentamos o top_n para ter mais candidatos a filtrar
        resultados = collection.query(
            query_embeddings=[embedding_pergunta],
            n_results=top_n,
            include=['documents', 'metadatas', 'distances']
        )
        
        chunks_relevantes_filtrados = []
        if resultados and resultados.get('ids')[0]:
            print(f"  - Encontrados {len(resultados['ids'][0])} chunks candidatos (antes do filtro de distância).")
            for i in range(len(resultados['ids'][0])):
                distancia = resultados['distances'][0][i]
                
                # <<< NOVO FILTRO DE DISTÂNCIA ADICIONADO AQUI >>>
                if distancia <= limiar_distancia:
                    texto_chunk = resultados['documents'][0][i]
                    metadados = resultados['metadatas'][0][i]
                    chunks_relevantes_filtrados.append({
                        "id_chunk_db": resultados['ids'][0][i],
                        "texto_chunk": texto_chunk,
                        "metadados": metadados,
                        "distancia": distancia
                    })
                    print(f"    - Chunk RELEVANTE (distância: {distancia:.4f}): '{texto_chunk[:100]}...'")
                else:
                    print(f"    - Chunk DESCARTADO por alta distância ({distancia:.4f}): '{resultados['documents'][0][i][:100]}...'")
        
        if not chunks_relevantes_filtrados:
            print("  - Nenhum chunk relevante encontrado dentro do limiar de distância.")
            
        return chunks_relevantes_filtrados

    except Exception as e:
        print(f"Erro ao consultar o ChromaDB: {e}")
        return []
    
OLLAMA_API_URL = "http://localhost:11434/api/generate" 
# Este é o endpoint padrão do Ollama para geração de texto

def gerar_resposta_com_llm(prompt: str, nome_modelo_llm: str) -> str:
    """
    Envia um prompt para o LLM via API do Ollama e retorna a resposta.
    """
    if not prompt.strip():
        return "Erro: Prompt vazio."

    print(f"\nEnviando prompt para o LLM ({nome_modelo_llm})...")
    # print(f"Prompt para depuração:\n---\n{prompt}\n---") # Descomente para ver o prompt exato

    payload = {
        "model": nome_modelo_llm,
        "prompt": prompt,
        "stream": False,  # Resposta completa de uma vez, para simplificar
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120) # Timeout de 120 segundos
        response.raise_for_status()  # Levanta um erro para códigos HTTP 4xx ou 5xx
        
        response_data = response.json()
        resposta_llm = response_data.get("response", "").strip()
        
        print("Resposta recebida do LLM.")
        return resposta_llm
        
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão/comunicação com a API do Ollama: {e}")
        return f"Erro ao contatar o LLM. Verifique se o Ollama está rodando e o modelo '{nome_modelo_llm}' está disponível. Erro: {e}"
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON da resposta do Ollama: {response.text}")
        return "Erro ao processar resposta do LLM."
    except Exception as e:
        print(f"Erro inesperado ao interagir com o LLM: {e}")
        return f"Erro inesperado com LLM: {e}"