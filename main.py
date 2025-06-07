# main.py
from src.database_manager import criar_tabela_documentos, inserir_documento
from src.pdf_processor import encontrar_pdfs, extrair_texto_pdf, calcular_hash_arquivo

PASTA_DOCUMENTOS = "documentos_para_catalogar"
TAMANHO_MAX_PREVIEW = 500 # Define o tamanho do preview

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
            
            hash_do_arquivo = calcular_hash_arquivo(pdf_path_obj)
            if not hash_do_arquivo:
                print(f"Não foi possível calcular o hash para {nome_do_arquivo}. Pulando este arquivo.")
                continue

            print(f"Hash SHA256: {hash_do_arquivo}")
            
            # Agora extrair_texto_pdf retorna o TEXTO COMPLETO
            texto_completo_extraido = extrair_texto_pdf(pdf_path_obj)
            
            # Criar o preview a partir do texto completo
            texto_preview_para_db = ""
            if texto_completo_extraido: # Verifica se não é None ou string vazia
                if texto_completo_extraido.startswith(("ERRO", "AVISO")):
                    # Se for uma mensagem de erro/aviso, usamos ela inteira como preview (geralmente são curtas)
                    texto_preview_para_db = texto_completo_extraido
                else:
                    # Caso contrário, criamos o preview normalmente
                    texto_preview_para_db = texto_completo_extraido[:TAMANHO_MAX_PREVIEW]
                    if len(texto_completo_extraido) > TAMANHO_MAX_PREVIEW:
                        texto_preview_para_db += "..."
            
            print(f"Preview do Texto: {texto_preview_para_db}") # Mostra o preview gerado

            inserir_documento(
                nome_arquivo=nome_do_arquivo,
                caminho_arquivo=caminho_completo_arquivo,
                texto_preview=texto_preview_para_db,      # Passa o preview gerado
                texto_completo=texto_completo_extraido, # Passa o texto completo
                hash_arquivo=hash_do_arquivo
            )
        
        print("\n--- Catalogação Concluída ---")