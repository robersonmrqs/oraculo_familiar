# perguntar_oraculo.py

from src.ia_processor import (
    buscar_chunks_relevantes,
    gerar_resposta_com_llm,
    inicializar_chroma,
    carregar_modelo_embedding
)

MODELO_LLM_OLLAMA = "llama3:instruct"

def formatar_prompt(pergunta_usuario: str, chunks_contexto: list[dict], historico_conversa: list[dict]) -> str:
    """
    Formata o prompt para o LLM com o histórico da conversa, a pergunta e os chunks de contexto.
    """
    # Formata o histórico da conversa para inclusão no prompt
    historico_formatado = ""
    if historico_conversa:
        historico_formatado += "--- INÍCIO DO HISTÓRICO DA CONVERSA ---\n"
        for turno in historico_conversa:
            role = "Usuário" if turno["role"] == "user" else "Oráculo"
            historico_formatado += f"{role}: {turno['content']}\n"
        historico_formatado += "--- FIM DO HISTÓRICO DA CONVERSA ---\n\n"

    contexto_str = "\n\n---\n\n".join([chunk.get('texto_chunk', '') for chunk in chunks_contexto])

    # A instrução inicial para o LLM
    instrucao_sistema = (
        "Você é um assistente prestativo do 'Oráculo Familiar'. "
        "Sua tarefa é responder a NOVA PERGUNTA do usuário baseando-se no CONTEXTO (extraído de documentos familiares) "
        "e no HISTÓRICO DA CONVERSA, se for relevante.\n"
        "Se a informação não estiver no CONTEXTO, diga 'Com base nos documentos fornecidos, não encontrei informações sobre isso.'.\n\n"
    )

    prompt = (
        instrucao_sistema +
        historico_formatado +
        f"CONTEXTO ATUAL (DOCUMENTOS RELEVANTES PARA A NOVA PERGUNTA):\n{contexto_str}\n\n"
        f"NOVA PERGUNTA: {pergunta_usuario}\n\n"
        "RESPOSTA:"
    )
    return prompt

def main():
    """Função principal que executa o loop de Pergunta e Resposta com memória."""
    print("Oráculo Familiar - Sistema de Pergunta e Resposta (com Memória)")
    print(f"Usando LLM: {MODELO_LLM_OLLAMA} via Ollama.")

    try:
        print("Inicializando componentes de IA...")
        carregar_modelo_embedding()
        inicializar_chroma()
        print("Componentes de IA prontos.")
    except Exception as e:
        print(f"Erro fatal durante a inicialização: {e}")
        return

    # Inicializa o histórico da conversa aqui, fora do loop
    historico_conversa = []

    while True:
        pergunta_usuario = input("\nQual sua pergunta sobre os documentos da família? (ou 'sair'): ")
        if pergunta_usuario.lower() in ['sair', 'exit', 'quit']:
            break
        if not pergunta_usuario.strip():
            continue

        # A busca de chunks ainda é baseada apenas na pergunta atual
        chunks_relevantes = buscar_chunks_relevantes(pergunta_usuario, top_n=5)

        # O prompt agora inclui o histórico da conversa
        prompt_para_llm = formatar_prompt(pergunta_usuario, chunks_relevantes, historico_conversa)
        
        resposta_llm = gerar_resposta_com_llm(prompt_para_llm, nome_modelo_llm=MODELO_LLM_OLLAMA)

        print("\n" + "="*25 + " RESPOSTA DO ORÁCULO " + "="*25)
        print(resposta_llm)
        print("="*72)

        # Adiciona a pergunta atual e a resposta ao histórico para a próxima rodada
        historico_conversa.append({"role": "user", "content": pergunta_usuario})
        historico_conversa.append({"role": "assistant", "content": resposta_llm})

        # Opcional: mostrar os documentos consultados (como antes)
        if chunks_relevantes:
            print("\n--- Documentos consultados para esta resposta: ---")
            for i, chunk_info in enumerate(chunks_relevantes):
                info_metadados = chunk_info.get('metadados', {})
                nome_arquivo = info_metadados.get('nome_arquivo_original', 'N/A')
                print(f"\n{i+1}. Trecho do Arquivo: '{nome_arquivo}'")
                print(f"   Conteúdo: \"{chunk_info.get('texto_chunk', '')[:250]}...\"")
            print("-" * 52)
        else:
            print("\n(Nenhum trecho específico de documento foi encontrado para esta pergunta)")
    
    print("\nOráculo Familiar encerrado. Até mais!")

if __name__ == "__main__":
    main()