# src/database_manager.py
"""
Módulo contendo a classe DatabaseManager para encapsular todas as interações
com o banco de dados SQLite.
"""
import config
import datetime
import sqlite3
from pathlib import Path

class DatabaseManager:
    """Gerencia a conexão e as operações com o banco de dados SQLite."""

    def __init__(self):
        """Inicializa o gerenciador e estabelece a conexão com o banco."""
        db_path = Path(config.DB_NOME_ARQUIVO)
        self.conn = sqlite3.connect(db_path)
        print(f"Conexão com o banco de dados '{config.DB_NOME_ARQUIVO}' estabelecida.")

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            print("Conexão com o banco de dados fechada.")

    def criar_tabela_documentos(self):
        """Cria a tabela 'documentos' se ela não existir."""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT NOT NULL,
            caminho_arquivo TEXT NOT NULL UNIQUE,
            texto_preview TEXT,
            texto_completo TEXT,
            data_catalogacao TIMESTAMP,
            hash_arquivo TEXT UNIQUE,
            indexado_no_chroma BOOLEAN DEFAULT 0
        )
        """)
        self.conn.commit()
        print("Tabela 'documentos' verificada/criada com sucesso.")

    def inserir_documento(self, nome_arquivo: str, caminho_arquivo: str,
                          texto_preview: str, texto_completo: str,
                          hash_arquivo: str) -> bool:
        """
        Insere um novo documento no banco. Retorna True se inseriu, False caso contrário.
        """
        try:
            cursor = self.conn.cursor()
            data_atual = datetime.datetime.now()
            cursor.execute(
                "INSERT INTO documentos (nome_arquivo, caminho_arquivo, texto_preview, texto_completo, data_catalogacao, hash_arquivo, indexado_no_chroma) VALUES (?, ?, ?, ?, ?, ?, 0)",
                (nome_arquivo, caminho_arquivo, texto_preview, texto_completo, data_atual, hash_arquivo)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Este não é um erro, apenas informa que o documento já existe.
            return False
        except Exception as e:
            print(f"  - ERRO ao inserir documento '{nome_arquivo}': {e}")
            return False

    def marcar_documento_como_indexado(self, doc_id: int):
        """Atualiza o status de um documento para indexado."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE documentos SET indexado_no_chroma = 1 WHERE id = ?", (doc_id,))
            self.conn.commit()
            print(f"  - Documento ID {doc_id} marcado como indexado.")
        except Exception as e:
            print(f"  - ERRO ao marcar documento ID {doc_id} como indexado: {e}")

    def obter_documentos_para_embedding(self) -> list:
        """Busca todos os documentos que ainda não foram indexados no ChromaDB."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, nome_arquivo, texto_completo FROM documentos WHERE texto_completo IS NOT NULL AND texto_completo != '' AND indexado_no_chroma = 0")
            documentos = cursor.fetchall()
            return documentos
        except Exception as e:
            print(f"  - ERRO ao obter documentos para embedding: {e}")
            return []