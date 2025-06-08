# src/database_manager.py
import datetime
import sqlite3
from pathlib import Path

NOME_BANCO_DADOS = "oraculo_familiar.db" # O arquivo do banco será criado na raiz do projeto

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    return sqlite3.connect(NOME_BANCO_DADOS)

def criar_tabela_documentos():
    """Cria a tabela 'documentos' com a nova coluna 'indexado_no_chroma'."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_arquivo TEXT NOT NULL,
        caminho_arquivo TEXT NOT NULL UNIQUE,
        texto_preview TEXT,
        texto_completo TEXT,
        data_catalogacao TIMESTAMP,
        hash_arquivo TEXT UNIQUE,
        indexado_no_chroma BOOLEAN DEFAULT 0 -- <<< NOVA COLUNA
    )
    """)
    conn.commit()
    conn.close()
    print("Tabela 'documentos' (com coluna de indexação) verificada/criada.")

def marcar_documento_como_indexado(doc_id: int):
    """Atualiza o status de um documento para indexado no ChromaDB."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE documentos SET indexado_no_chroma = 1 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    print(f"  - Documento ID {doc_id} marcado como indexado.")

def inserir_documento(nome_arquivo: str, caminho_arquivo: str, 
                      texto_preview: str, texto_completo: str,
                      hash_arquivo: str = None) -> bool: # Adiciona o tipo de retorno
    """
    Insere um novo documento. Retorna True se inseriu, False caso contrário.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    data_atual = datetime.datetime.now()

    try:
        cursor.execute(
            "INSERT INTO documentos (nome_arquivo, caminho_arquivo, texto_preview, texto_completo, data_catalogacao, hash_arquivo, indexado_no_chroma) VALUES (?, ?, ?, ?, ?, ?, 0)",
            (nome_arquivo, caminho_arquivo, texto_preview, texto_completo, data_atual, hash_arquivo)
        )
        conn.commit()
        print(f"  - SUCESSO: Documento '{nome_arquivo}' inserido no banco de dados.")
        return True # Retorna True em caso de sucesso
    except sqlite3.IntegrityError:
        print(f"  - AVISO: Documento '{nome_arquivo}' já existe no banco (conflito de hash ou caminho).")
        return False # Retorna False se já existia
    except Exception as e:
        print(f"  - ERRO ao inserir documento '{nome_arquivo}': {e}")
        return False # Retorna False em caso de outro erro
    finally:
        if conn:
            conn.close()

def db_fechado_corretamente():
    """Verifica se não há um arquivo de journal, indicando um fechamento limpo."""
    journal_path = Path(__file__).resolve().parent.parent / f"{NOME_BANCO_DADOS}-journal"
    return not journal_path.exists()