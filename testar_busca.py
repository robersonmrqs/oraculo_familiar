# testar_busca.py
from src.ia_processor import buscar_chunks_relevantes, inicializar_chroma, carregar_modelo_embedding

def main():
    print("Inicializando sistema para teste de busca...")
    # É bom carregar/inicializar tudo uma vez no início
    carregar_modelo_embedding() 
    try:
        inicializar_chroma()
    except Exception as e:
        print(f"Falha ao inicializar ChromaDB. Abortando. Erro: {e}")
        return

    while True:
        pergunta = input("\nDigite sua pergunta (ou 'sair' para terminar): ")
        if pergunta.lower() == 'sair':
            break
        if not pergunta.strip():
            continue

        chunks_relevantes = buscar_chunks_relevantes(pergunta, top_n=3)

        if chunks_relevantes:
            print("\n--- Chunks Mais Relevantes Encontrados ---")
            for i, chunk_info in enumerate(chunks_relevantes):
                print(f"\n{i+1}. Chunk (do Doc ID: {chunk_info['metadados'].get('doc_id_original', 'N/A')}, Arquivo: {chunk_info['metadados'].get('nome_arquivo_original', 'N/A')})")
                print(f"   Distância: {chunk_info['distancia']:.4f}")
                print(f"   Texto: {chunk_info['texto_chunk']}")
        else:
            print("Nenhuma informação relevante encontrada para esta pergunta.")

    print("Teste de busca finalizado.")

if __name__ == "__main__":
    main()