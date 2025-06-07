# perguntar_oraculo.py
# Arquivo principal para interagir com o Oráculo Familiar

from src.ia_processor import (
    buscar_chunks_relevantes,
    gerar_resposta_com_llm,
    inicializar_chroma,
    carregar_modelo_embedding
)

# Defina o modelo LLM que você tem rodando e quer usar!
# Se no futuro você usar outro modelo (ex: phi3, gemma, etc.), altere esta linha.
MODELO_LLM_OLLAMA = "llama3:instruct"

def formatar_prompt(pergunta_usuario: str, chunks_contexto: list[dict]) -> str:
    """
    Formata o prompt para o LLM com a pergunta e os chunks de contexto.
    """
    # Se a busca no ChromaDB não retornou nenhum chunk relevante
    if not chunks_contexto:
        # Você pode optar por não chamar o LLM e simplesmente responder que não encontrou nada.
        # Ou, como aqui, pedir ao LLM para usar seu conhecimento geral, embora seja menos útil para nosso caso.
        # A melhor abordagem é a instrução no prompt principal. Este é um fallback.
        return f"Pergunta: {pergunta_usuario}\n\nResponda à pergunta."

    # Concatena o texto de todos os chunks encontrados, separados por "---"
    contexto_str = "\n\n---\n\n".join([chunk.get('texto_chunk', '') for chunk in chunks_contexto])

    prompt = (
        "Você é um assistente prestativo do 'Oráculo Familiar'. "
        "Sua tarefa é responder a PERGUNTA do usuário baseando-se estritamente no CONTEXTO fornecido, que foi extraído de documentos familiares. "
        "Seja direto e factual.\n"
        "Se a informação para responder à pergunta não estiver explicitamente no CONTEXTO, diga 'Com base nos documentos fornecidos, não encontrei informações sobre isso.'. "
        "Não invente respostas.\n\n"
        f"CONTEXTO:\n{contexto_str}\n\n"
        f"PERGUNTA: {pergunta_usuario}\n\n"
        "RESPOSTA:"
    )
    return prompt

def main():
    """Função principal que executa o loop de Pergunta e Resposta."""
    print("Oráculo Familiar - Sistema de Pergunta e Resposta")
    print(f"Usando LLM: {MODELO_LLM_OLLAMA} via Ollama.")
    print("Certifique-se que o serviço Ollama está rodando em segundo plano.")

    # Inicialização dos componentes
    try:
        print("Inicializando componentes de IA (pode levar um momento)...")
        carregar_modelo_embedding()
        inicializar_chroma()
        print("Componentes de IA prontos.")
    except Exception as e:
        print(f"Erro fatal durante a inicialização: {e}")
        return

    # Loop principal para receber perguntas
    while True:
        pergunta_usuario = input("\nQual sua pergunta sobre os documentos da família? (ou 'sair'): ")
        if pergunta_usuario.lower() in ['sair', 'exit', 'quit']:
            break
        if not pergunta_usuario.strip():
            continue

        # 1. Buscar os chunks mais relevantes no ChromaDB
        chunks_relevantes = buscar_chunks_relevantes(pergunta_usuario, top_n=5, limiar_distancia=0.7) 

        # 2. Formatar o prompt para enviar ao LLM
        prompt_para_llm = formatar_prompt(pergunta_usuario, chunks_relevantes)

        # 3. Gerar a resposta final usando o LLM
        resposta_llm = gerar_resposta_com_llm(prompt_para_llm, nome_modelo_llm=MODELO_LLM_OLLAMA)

        # 4. Exibir os resultados para o usuário
        print("\n" + "="*25 + " RESPOSTA DO ORÁCULO " + "="*25)
        print(resposta_llm)
        print("="*72)

        if chunks_relevantes:
            print("\n--- Documentos consultados para esta resposta: ---")
            for i, chunk_info in enumerate(chunks_relevantes):
                # Código robusto para acessar metadados usando .get()
                info_metadados = chunk_info.get('metadados', {})
                nome_arquivo = info_metadados.get('nome_arquivo_original', 'N/A')
                doc_id = info_metadados.get('doc_id_original', 'N/A')
                chunk_idx = info_metadados.get('indice_chunk', 'N/A')
                distancia = chunk_info.get('distancia', 0.0)
                texto_chunk = chunk_info.get('texto_chunk', '')

                print(f"\n{i+1}. Trecho do Arquivo: '{nome_arquivo}' (Doc ID: {doc_id}, Chunk: {chunk_idx})")
                print(f"   Distância da pergunta: {distancia:.4f}")
                print(f"   Conteúdo do trecho: \"{texto_chunk[:200]}...\"")
            print("-" * 52)
        else:
            print("\n(Nenhum trecho específico de documento foi considerado altamente relevante para esta pergunta)")

    print("\nOráculo Familiar encerrado. Até mais!")

if __name__ == "__main__":
    # Este bloco garante que o código dentro dele só roda quando o script é executado diretamente
    main()