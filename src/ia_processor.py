# src/ia_processor.py
import sqlite3
from pathlib import Path
from sentence_transformers import SentenceTransformer

NOME_BANCO_DADOS = "oraculo_familiar.db"

MODELO_EMBEDDING = 'paraphrase-multilingual-MiniLM-L12-v2'
model = None # Vamos carregar o modelo sob demanda

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