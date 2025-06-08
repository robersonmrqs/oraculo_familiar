# src/oraculo_core.py

# Importa as funções do nosso processador de IA
from src.ia_processor import (
    buscar_chunks_relevantes,
    gerar_resposta_com_llm
)

# O modelo LLM que vamos usar
MODELO_LLM_OLLAMA = "llama3:instruct"

def formatar_prompt(pergunta_usuario: str, chunks_contexto: list[dict], historico_conversa: list[dict]) -> str:
    """
    Formata o prompt para o LLM com o histórico, a pergunta e o contexto.
    (Esta função é idêntica à que tínhamos em perguntar_oraculo.py)
    """
    historico_formatado = ""
    if historico_conversa:
        historico_formatado += "--- INÍCIO DO HISTÓRICO DA CONVERSA ---\n"
        for turno in historico_conversa:
            role = "Usuário" if turno["role"] == "user" else "Oráculo"
            historico_formatado += f"{role}: {turno['content']}\n"
        historico_formatado += "--- FIM DO HISTÓRICO DA CONVERSA ---\n\n"

    contexto_str = "\n\n---\n\n".join([chunk.get('texto_chunk', '') for chunk in chunks_contexto])

    instrucao_sistema = (
        "Você é Jarvis, um assistente de IA prestativo e espirituoso do 'Oráculo Familiar'. "
        "Sua tarefa é responder a NOVA PERGUNTA do usuário com precisão, baseando-se estritamente no CONTEXTO (extraído de documentos familiares) "
        "e no HISTÓRICO DA CONVERSA.\n"
        "Se a informação não estiver no CONTEXTO, diga 'Com base nos documentos disponíveis, não possuo dados sobre isso.'. "
        "Mantenha um tom profissional, mas com um toque sutil de sagacidade.\n\n"
    )

    prompt = (
        instrucao_sistema +
        historico_formatado +
        f"CONTEXTO ATUAL (DOCUMENTOS RELEVANTES PARA A NOVA PERGUNTA):\n{contexto_str}\n\n"
        f"NOVA PERGUNTA: {pergunta_usuario}\n\n"
        "RESPOSTA:"
    )
    return prompt

def processar_pergunta(pergunta_usuario: str, historico_conversa: list[dict]) -> str:
    """
    Função principal que encapsula todo o fluxo de RAG para uma única pergunta.
    """
    print(f"Processando pergunta: '{pergunta_usuario}'")
    
    # 1. Buscar chunks relevantes no ChromaDB
    chunks_relevantes = buscar_chunks_relevantes(pergunta_usuario, top_n=5)

    # 2. Formatar o prompt para o LLM
    prompt_para_llm = formatar_prompt(pergunta_usuario, chunks_relevantes, historico_conversa)
    
    # 3. Gerar resposta com o LLM
    resposta_llm = gerar_resposta_com_llm(prompt_para_llm, nome_modelo_llm=MODELO_LLM_OLLAMA)

    return resposta_llm