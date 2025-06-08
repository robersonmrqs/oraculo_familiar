# verificar_texto.py
# Versão de diagnóstico aprimorada

import sqlite3
import sys
from pathlib import Path

def buscar_texto_completo(nome_arquivo_alvo: str):
    """
    Busca e exibe o status completo de um documento no banco de dados.
    """
    db_path = Path(__file__).resolve().parent / "oraculo_familiar.db"
    if not db_path.exists():
        print(f"Erro: Arquivo do banco de dados '{db_path}' não encontrado.")
        print("Você já executou o script 'atualizar_oraculo.py'?")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Usamos LIKE para o caso de você não digitar o nome exato do arquivo
    # Agora também selecionamos o status de indexação
    cursor.execute(
        "SELECT id, nome_arquivo, indexado_no_chroma, texto_completo FROM documentos WHERE nome_arquivo LIKE ?",
        (f"%{nome_arquivo_alvo}%",)
    )
    
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(f"Nenhum documento encontrado no banco de dados com o nome contendo '{nome_arquivo_alvo}'.")
        print("Verifique se o arquivo está na pasta 'documentos_para_catalogar' e se o script 'atualizar_oraculo.py' foi executado sem erros.")
        return
    
    print(f"Encontrados {len(resultados)} documento(s) correspondente(s):")
    
    for doc_id, nome_arquivo, indexado, texto_completo in resultados:
        print("\n" + "="*80)
        print(f"Relatório do Documento ID: {doc_id}")
        print(f"Nome do Arquivo: {nome_arquivo}")
        status_indexacao = "Sim (1)" if indexado else "Não (0)"
        print(f"Foi indexado para a IA? {status_indexacao}")
        print("="*80)
        print("\n--- TEXTO COMPLETO EXTRAÍDO (OCR) ---")
        if texto_completo and texto_completo.strip():
            print(texto_completo)
        else:
            print("!!! NENHUM TEXTO FOI EXTRAÍDO DESTE DOCUMENTO !!!")
        print("\n--- FIM DO TEXTO ---")
        print("="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python verificar_texto.py \"parte_do_nome_do_arquivo.pdf\"")
        print("Exemplo: python verificar_texto.py \"cpfl\"")
        sys.exit(1)
    
    nome_alvo = sys.argv[1]
    buscar_texto_completo(nome_alvo)