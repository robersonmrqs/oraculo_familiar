# src/database_manager.py
import datetime
import sqlite3
from pathlib import Path

NOME_BANCO_DADOS = "oraculo_familiar.db" # O arquivo do banco será criado na raiz do projeto

def conectar_db():
    """Conecta ao banco de dados SQLite e retorna o objeto de conexão."""
    return sqlite3.connect(NOME_BANCO_DADOS)

def criar_tabela_documentos():
    """Cria a tabela 'documentos' se ela não existir."""
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
        hash_arquivo TEXT UNIQUE 
    )
    """)
    conn.commit()
    conn.close()
    print("Tabela 'documentos' verificada/criada com sucesso.")

def inserir_documento(nome_arquivo: str, caminho_arquivo: str, 
                      texto_preview: str, texto_completo: str,
                      hash_arquivo: str = None):
    """
    Insere um novo documento na tabela 'documentos', incluindo o texto completo.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    data_atual = datetime.datetime.now()

    try:
        cursor.execute("""
        INSERT INTO documentos (nome_arquivo, caminho_arquivo, texto_preview, texto_completo, data_catalogacao, hash_arquivo)
        VALUES (?, ?, ?, ?, ?, ?) 
        """, (nome_arquivo, caminho_arquivo, texto_preview, texto_completo, data_atual, hash_arquivo)) # <<< VALORES ATUALIZADOS
        conn.commit()
        print(f"Documento '{nome_arquivo}' inserido com sucesso (com texto completo).")
    except sqlite3.IntegrityError:
        print(f"Documento '{nome_arquivo}' (caminho: {caminho_arquivo}) já existe no banco de dados ou conflito de hash.")
    except Exception as e:
        print(f"Erro ao inserir documento '{nome_arquivo}': {e}")
    finally:
        conn.close()