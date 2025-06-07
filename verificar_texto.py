# verificar_texto.py
import sqlite3
import sys
from pathlib import Path

def buscar_texto_completo(nome_arquivo_alvo: str):
    """Busca e exibe o texto completo de um documento no banco de dados."""
    db_path = Path(__file__).resolve().parent / "oraculo_familiar.db"
    if not db_path.exists():
        print(f"Erro: Arquivo do banco de dados '{db_path}' não encontrado.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Usamos LIKE para o caso de você não digitar o nome exato do arquivo
    cursor.execute(
        "SELECT nome_arquivo, texto_completo FROM documentos WHERE nome_arquivo LIKE ?",
        (f"%{nome_arquivo_alvo}%",)
    )

    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(f"Nenhum documento encontrado com o nome contendo '{nome_arquivo_alvo}'.")
        return

    for nome_arquivo, texto_completo in resultados:
        print("\n" + "="*80)
        print(f"Documento Encontrado: {nome_arquivo}")
        print("="*80)
        print("\n--- TEXTO COMPLETO EXTRAÍDO ---")
        print(texto_completo)
        print("\n--- FIM DO TEXTO ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python verificar_texto.py \"parte_do_nome_do_arquivo.pdf\"")
        sys.exit(1)

    nome_alvo = sys.argv[1]
    buscar_texto_completo(nome_alvo)