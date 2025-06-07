# main.py
from src.database_manager import criar_tabela_documentos, inserir_documento
from src.pdf_processor import encontrar_pdfs, extrair_texto_pdf

PASTA_DOCUMENTOS = "documentos_para_catalogar"

if __name__ == "__main__":
    print("Iniciando o Oráculo Familiar - Catalogador")
    criar_tabela_documentos()

    lista_de_pdfs = encontrar_pdfs(PASTA_DOCUMENTOS)

    if not lista_de_pdfs:
        print("Nenhum PDF encontrado para processar.")
    else:
        print(f"\n--- Processando {len(lista_de_pdfs)} PDFs para catalogação ---")
        for pdf_path_obj in lista_de_pdfs: # Renomeei para pdf_path_obj para clareza
            nome_do_arquivo = pdf_path_obj.name
            caminho_completo_arquivo = str(pdf_path_obj.resolve()) # str() para garantir tipo correto

            print(f"\nProcessando: {nome_do_arquivo}")
            
            texto_preview_extraido = extrair_texto_pdf(pdf_path_obj)
            print(f"Preview do Texto: {texto_preview_extraido[:100]}...")

            inserir_documento(
                nome_arquivo=nome_do_arquivo,
                caminho_arquivo=caminho_completo_arquivo,
                texto_preview=texto_preview_extraido,
                hash_arquivo=None # Deixaremos o hash para o próximo passo
            )
        
        print("\n--- Catalogação Concluída ---")