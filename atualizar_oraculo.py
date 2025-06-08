# atualizar_oraculo.py
# Versão com logging aprimorado para depuração

import os
from pathlib import Path
from src.database_manager import criar_tabela_documentos, inserir_documento, db_fechado_corretamente
from src.pdf_processor import encontrar_pdfs, calcular_hash_arquivo, extrair_texto_pdf
from src.ia_processor import obter_documentos_para_embedding, dividir_texto_em_chunks, gerar_embeddings_para_chunks, adicionar_chunks_ao_chroma

PASTA_DOCUMENTOS = "documentos_para_catalogar"
TAMANHO_MAX_PREVIEW = 500

def catalogar_novos_documentos():
    """Encontra novos PDFs na pasta, extrai dados e salva no SQLite."""
    print("\n--- Etapa 1: Catalogando novos documentos ---")
    criar_tabela_documentos()
    lista_de_pdfs = encontrar_pdfs(PASTA_DOCUMENTOS)
    
    if not lista_de_pdfs:
        print("-> Nenhum arquivo PDF (.pdf ou .PDF) encontrado na pasta de catalogação.")
        return
        
    print(f"-> Encontrados {len(lista_de_pdfs)} arquivos PDF para verificar.")
    for pdf in lista_de_pdfs:
        print(f"  - {pdf.name}")

    novos_documentos_adicionados = 0
    for pdf_path_obj in lista_de_pdfs:
        print("-" * 20)
        print(f"Processando arquivo: {pdf_path_obj.name}")
        
        try:
            hash_do_arquivo = calcular_hash_arquivo(pdf_path_obj)
            if not hash_do_arquivo:
                print(f"  - ERRO: Não foi possível calcular o hash. Pulando arquivo.")
                continue
            
            print(f"  - Hash calculado: {hash_do_arquivo[:10]}...")

            print("  - Extraindo texto (pode demorar se precisar de OCR)...")
            texto_completo = extrair_texto_pdf(pdf_path_obj)
            
            if not texto_completo or texto_completo.startswith(("ERRO", "AVISO")):
                print(f"  - AVISO: Não foi possível extrair texto legível. '{texto_completo or 'Nenhum texto'}'")
                texto_preview = texto_completo
            else:
                print(f"  - Texto extraído com sucesso ({len(texto_completo)} caracteres).")
                texto_preview = texto_completo[:TAMANHO_MAX_PREVIEW] + ("..." if len(texto_completo) > TAMANHO_MAX_PREVIEW else "")

            inserido_com_sucesso = inserir_documento(
                nome_arquivo=pdf_path_obj.name,
                caminho_arquivo=str(pdf_path_obj.resolve()),
                texto_preview=texto_preview,
                texto_completo=texto_completo,
                hash_arquivo=hash_do_arquivo
            )
            
            if inserido_com_sucesso:
                novos_documentos_adicionados += 1

        except Exception as e:
            print(f"  - ERRO CRÍTICO ao processar o arquivo {pdf_path_obj.name}: {e}")
            
    print(f"--- Fim da Etapa 1: {novos_documentos_adicionados} novo(s) documento(s) adicionado(s) ao banco de dados. ---")


def indexar_novos_documentos():
    """Busca documentos não indexados, gera embeddings e salva no ChromaDB."""
    print("\n--- Etapa 2: Indexando documentos para a IA (gerando embeddings) ---")
    documentos_para_indexar = obter_documentos_para_embedding()
    
    if not documentos_para_indexar:
        print("-> Nenhum documento novo para indexar.")
        return

    print(f"-> Encontrados {len(documentos_para_indexar)} novos documentos para indexar na IA.")
    
    for doc_id, nome_arquivo, texto_completo in documentos_para_indexar:
        print("-" * 20)
        print(f"Indexando Documento ID: {doc_id}, Nome: {nome_arquivo}")
        
        if not texto_completo or not texto_completo.strip():
            print(f"  - AVISO: Documento sem texto completo. Pulando indexação.")
            continue

        chunks = dividir_texto_em_chunks(texto_completo)
        if not chunks:
            print(f"  - AVISO: Não foram gerados chunks. Pulando indexação.")
            continue
        
        print(f"  - Texto dividido em {len(chunks)} chunks.")
        
        embeddings_dos_chunks = gerar_embeddings_para_chunks(chunks)
        
        if embeddings_dos_chunks:
            adicionar_chunks_ao_chroma(
                doc_id=doc_id,
                nome_arquivo=nome_arquivo,
                chunks_texto=chunks,
                embeddings_vetores=embeddings_dos_chunks
            )
            
    print("--- Fim da Etapa 2: Indexação para a IA concluída. ---")


if __name__ == "__main__":
    print("Iniciando rotina de atualização do Oráculo Familiar...")
    # Precisamos ajustar a função inserir_documento para nos dizer se funcionou
    # Vamos fazer isso no database_manager.py
    
    # Adicionando uma verificação de segurança
    if not db_fechado_corretamente():
        print("\nAVISO: O banco de dados pode não ter sido fechado corretamente na última execução.")
        print("Se encontrar problemas, apagar o arquivo oraculo_familiar.db-journal pode ajudar.")

    catalogar_novos_documentos()
    indexar_novos_documentos()
    print("\nRotina de atualização do Oráculo finalizada!")