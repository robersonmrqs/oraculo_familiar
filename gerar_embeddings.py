# gerar_embeddings.py
from src.ia_processor import (
    obter_documentos_para_embedding,
    dividir_texto_em_chunks,
    gerar_embeddings_para_chunks
)

def main():
    print("Iniciando processo de geração de embeddings...")

    documentos = obter_documentos_para_embedding()
    if not documentos:
        print("Nenhum documento com texto completo encontrado para processar.")
        return

    print(f"Encontrados {len(documentos)} documentos para processar.")

    todos_os_embeddings_documentos = [] # Para armazenar todos os embeddings e referências

    for doc_id, nome_arquivo, texto_completo in documentos:
        print(f"\nProcessando Documento ID: {doc_id}, Nome: {nome_arquivo}")

        if not texto_completo.strip(): # Pula se texto_completo for vazio ou só espaços
            print(f"  - Documento ID: {doc_id} não possui texto completo. Pulando.")
            continue

        chunks = dividir_texto_em_chunks(texto_completo, tamanho_chunk=512, sobreposicao=64)
        if not chunks:
            print(f"  - Não foram gerados chunks para o Documento ID: {doc_id}. Pulando.")
            continue

        print(f"  - Texto dividido em {len(chunks)} chunks.")

        embeddings_dos_chunks = gerar_embeddings_para_chunks(chunks) # Retorna lista de listas de float

        # Por enquanto, vamos apenas imprimir informações sobre os embeddings gerados
        # e armazená-los em uma estrutura em memória (temporariamente)
        for i, embedding in enumerate(embeddings_dos_chunks):
            # Guardaríamos o doc_id, o chunk_id (ou índice), o texto do chunk e o embedding
            todos_os_embeddings_documentos.append({
                "doc_id": doc_id,
                "chunk_index": i,
                "texto_chunk": chunks[i][:100] + "...", # Preview do chunk
                "embedding_dim": len(embedding) # Dimensão do vetor de embedding
            })
            if i == 0: # Imprimir info apenas do primeiro chunk/embedding para não poluir muito
                print(f"    - Chunk {i} (preview): '{chunks[i][:50]}...'")
                print(f"    - Dimensão do embedding: {len(embedding)}")
                # print(f"    - Embedding (primeiros 5 valores): {embedding[:5]}")

    print(f"\n\nProcessamento concluído. Total de {len(todos_os_embeddings_documentos)} embeddings gerados.")
    if todos_os_embeddings_documentos:
        print("Exemplo de dados de embedding armazenados (em memória):")
        print(todos_os_embeddings_documentos[0])

if __name__ == "__main__":
    main()