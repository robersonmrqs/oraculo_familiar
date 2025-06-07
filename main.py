# main.py
from src.database_manager import criar_tabela_documentos
from src.pdf_processor import encontrar_pdfs, extrair_texto_pdf

PASTA_DOCUMENTOS = "documentos_para_catalogar"

if __name__ == "__main__":
    print("Iniciando o Oráculo Familiar - Catalogador")
    criar_tabela_documentos()

    lista_de_pdfs = encontrar_pdfs(PASTA_DOCUMENTOS)

    if not lista_de_pdfs:
        print("Nenhum PDF encontrado para processar.")
    else:
        print(f"\n--- Processando {len(lista_de_pdfs)} PDFs ---")
        for pdf_path in lista_de_pdfs:
            print(f"\nProcessando: {pdf_path.name}")
            texto = extrair_texto_pdf(pdf_path)
            print(f"Preview do Texto: {texto[:100]}...")