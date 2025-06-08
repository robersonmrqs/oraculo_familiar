# atualizar_oraculo.py
"""
Script único e principal para catalogar novos PDFs e indexá-los para a IA.
Este é o script a ser executado para atualizar a base de conhecimento do Oráculo.
"""
import config
from src.database_manager import DatabaseManager
from src.ia_processor import dividir_texto_em_chunks, gerar_embeddings_para_chunks, adicionar_chunks_ao_chroma
from src.pdf_processor import encontrar_pdfs, calcular_hash_arquivo, extrair_texto_pdf

def catalogar_novos_documentos(db_manager: DatabaseManager):
    """Encontra novos PDFs na pasta, extrai dados e salva no SQLite."""
    print("\n--- Etapa 1: Catalogando novos documentos ---")
    lista_de_pdfs = encontrar_pdfs(config.PASTA_DOCUMENTOS)
    
    if not lista_de_pdfs:
        print("-> Nenhum arquivo PDF encontrado na pasta.")
        return
        
    print(f"-> Encontrados {len(lista_de_pdfs)} arquivos PDF para verificar.")
    novos_documentos_adicionados = 0
    
    for pdf_path in lista_de_pdfs:
        print(f"\nVerificando: {pdf_path.name}")
        hash_do_arquivo = calcular_hash_arquivo(pdf_path)
        if not hash_do_arquivo: continue

        texto_completo = extrair_texto_pdf(pdf_path)
        texto_preview = texto_completo[:config.TAMANHO_MAX_PREVIEW] + "..." if texto_completo else ""

        if db_manager.inserir_documento(pdf_path.name, str(pdf_path.resolve()), texto_preview, texto_completo, hash_do_arquivo):
            print(f"  - SUCESSO: Documento '{pdf_path.name}' catalogado.")
            novos_documentos_adicionados += 1
        else:
            print(f"  - INFO: Documento '{pdf_path.name}' já existia no banco de dados.")
            
    print(f"--- Fim da Etapa 1: {novos_documentos_adicionados} novo(s) documento(s) adicionado(s). ---")

def indexar_novos_documentos(db_manager: DatabaseManager):
    """Busca documentos não indexados, gera embeddings e salva no ChromaDB."""
    print("\n--- Etapa 2: Indexando documentos para a IA ---")
    documentos_para_indexar = db_manager.obter_documentos_para_embedding()
    
    if not documentos_para_indexar:
        print("-> Nenhum documento novo para indexar.")
        return

    print(f"-> Encontrados {len(documentos_para_indexar)} novos documentos para indexar.")
    
    for doc_id, nome_arquivo, texto_completo in documentos_para_indexar:
        print(f"\nIndexando Documento ID: {doc_id}, Nome: {nome_arquivo}")
        if not texto_completo or not texto_completo.strip():
            print("  - AVISO: Documento sem texto. Pulando.")
            continue

        chunks = dividir_texto_em_chunks(texto_completo)
        if not chunks:
            print("  - AVISO: Não foram gerados chunks. Pulando.")
            continue
        
        embeddings = gerar_embeddings_para_chunks(chunks)
        if embeddings:
            adicionar_chunks_ao_chroma(doc_id, nome_arquivo, chunks, embeddings)
            db_manager.marcar_documento_como_indexado(doc_id)
            
    print("--- Fim da Etapa 2: Indexação para a IA concluída. ---")

def main():
    """Função principal que orquestra todo o processo de atualização."""
    print("Iniciando rotina de atualização do Oráculo Familiar...")
    db_manager = None
    try:
        db_manager = DatabaseManager()
        db_manager.criar_tabela_documentos()
        catalogar_novos_documentos(db_manager)
        indexar_novos_documentos(db_manager)
        print("\nRotina de atualização do Oráculo finalizada com sucesso!")
    except Exception as e:
        print(f"\nERRO CRÍTICO DURANTE A ATUALIZAÇÃO: {e}")
    finally:
        if db_manager:
            db_manager.close()

if __name__ == "__main__":
    main()