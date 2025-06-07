# gerar_embeddings.py
from pathlib import Path
from src.ia_processor import (
    obter_documentos_para_embedding,
    dividir_texto_em_chunks,
    gerar_embeddings_para_chunks,
    adicionar_chunks_ao_chroma, # <<< Novo import
    inicializar_chroma,         # <<< Novo import (para garantir que a pasta e coleção sejam criadas no início)
    CHROMA_DATA_PATH # <<< IMPORTE A CONSTANTE AQUI
)

def main():
    print("Iniciando processo de geração e armazenamento de embeddings no ChromaDB...")
    
    # Inicializa o ChromaDB (cria pasta e coleção se não existirem)
    # Isso é bom para garantir que está tudo pronto antes do loop
    try:
        inicializar_chroma()
    except Exception as e:
        print(f"Falha ao inicializar ChromaDB. Abortando. Erro: {e}")
        return

    documentos = obter_documentos_para_embedding()
    if not documentos:
        print("Nenhum documento com texto completo encontrado para processar.")
        return

    print(f"Encontrados {len(documentos)} documentos para processar.")
    total_chunks_processados = 0

    for doc_id, nome_arquivo, texto_completo in documentos:
        print(f"\nProcessando Documento ID: {doc_id}, Nome: {nome_arquivo}")
        
        if not texto_completo or not texto_completo.strip():
            print(f"  - Documento ID: {doc_id} não possui texto completo válido. Pulando.")
            continue

        chunks = dividir_texto_em_chunks(texto_completo, tamanho_chunk=512, sobreposicao=64)
        if not chunks:
            print(f"  - Não foram gerados chunks para o Documento ID: {doc_id}. Pulando.")
            continue
        
        print(f"  - Texto dividido em {len(chunks)} chunks.")
        
        embeddings_dos_chunks = gerar_embeddings_para_chunks(chunks)
        
        if embeddings_dos_chunks and len(embeddings_dos_chunks) == len(chunks):
            adicionar_chunks_ao_chroma(
                doc_id=doc_id,
                nome_arquivo=nome_arquivo,
                chunks_texto=chunks,
                embeddings_vetores=embeddings_dos_chunks
            )
            total_chunks_processados += len(chunks)
        else:
            print(f"  - ERRO: Não foi possível gerar ou alinhar embeddings para os chunks do doc ID {doc_id}.")
            
    print(f"\n\nProcessamento e armazenamento no ChromaDB concluídos.")
    print(f"Total de {total_chunks_processados} chunks processados e armazenados/atualizados.")
    print(f"Os dados do ChromaDB estão salvos em: '{Path(__file__).resolve().parent / CHROMA_DATA_PATH}'")


if __name__ == "__main__":
    main()