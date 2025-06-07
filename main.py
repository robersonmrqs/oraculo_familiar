# main.py
from src.pdf_processor import encontrar_pdfs

PASTA_DOCUMENTOS = "documentos_para_catalogar"

if __name__ == "__main__":
    print("Iniciando o Oráculo Familiar - Catalogador")
    lista_de_pdfs = encontrar_pdfs(PASTA_DOCUMENTOS)

    if not lista_de_pdfs:
        print("Nenhum PDF encontrado para processar.")
    else:
        print(f"\nTotal de {len(lista_de_pdfs)} PDFs a serem processados (exemplo).")