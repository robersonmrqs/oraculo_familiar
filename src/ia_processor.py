# src/ia_processor.py
import chromadb
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