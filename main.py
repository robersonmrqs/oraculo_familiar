# main.py
from src.database_manager import criar_tabela_documentos, inserir_documento
from src.pdf_processor import encontrar_pdfs, extrair_texto_pdf, calcular_hash_arquivo

PASTA_DOCUMENTOS = "documentos_para_catalogar"

if __name__ == "__main__":
    print("Iniciando o Oráculo Familiar - Catalogador")
    criar_tabela_documentos()

    lista_de_pdfs = encontrar_pdfs(PASTA_DOCUMENTOS)

    if not lista_de_pdfs:
        print("Nenhum PDF encontrado para processar.")
    else:
        print(f"\n--- Processando {len(lista_de_pdfs)} PDFs para catalogação ---")
        for pdf_path_obj in lista_de_pdfs:
            nome_do_arquivo = pdf_path_obj.name
            caminho_completo_arquivo = str(pdf_path_obj.resolve())

            print(f"\nProcessando: {nome_do_arquivo} (Caminho: {caminho_completo_arquivo})")
            
            # 1. Calcular o hash ANTES de qualquer processamento pesado
            hash_do_arquivo = calcular_hash_arquivo(pdf_path_obj)
            if not hash_do_arquivo:
                print(f"Não foi possível calcular o hash para {nome_do_arquivo}. Pulando este arquivo.")
                continue # Pula para o próximo PDF

            print(f"Hash SHA256: {hash_do_arquivo}")
            
            texto_preview_extraido = extrair_texto_pdf(pdf_path_obj)

            inserir_documento(
                nome_arquivo=nome_do_arquivo,
                caminho_arquivo=caminho_completo_arquivo,
                texto_preview=texto_preview_extraido,
                hash_arquivo=hash_do_arquivo # Agora passamos o hash!
            )
        
        print("\n--- Catalogação Concluída ---")