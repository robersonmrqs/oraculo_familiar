# src/database_manager.py
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
        data_catalogacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hash_arquivo TEXT UNIQUE 
    )
    """)
    conn.commit()
    conn.close()
    print("Tabela 'documentos' verificada/criada com sucesso.")