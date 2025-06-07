# perguntar_oraculo.py
from src.ia_processor import (
    buscar_chunks_relevantes, 
    gerar_resposta_com_llm,
    inicializar_chroma,
    carregar_modelo_embedding
)

# Defina o modelo LLM que você tem rodando e quer usar!
MODELO_LLM_OLLAMA = "llama3:instruct" 

def formatar_prompt(pergunta_usuario: str, chunks_contexto: list[dict]) -> str:
    """
    Formata o prompt para o LLM com a pergunta e os chunks de contexto.
    """
    if not chunks_contexto:
        return f"Pergunta: {pergunta_usuario}\n\nResponda à pergunta com base no seu conhecimento geral, pois não encontrei documentos relevantes."

    contexto_str = "\n\n---\n\n".join([chunk['texto_chunk'] for chunk in chunks_contexto])
    
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
    print("Oráculo Familiar - Sistema de Pergunta e Resposta")
    print(f"Usando LLM: {MODELO_LLM_OLLAMA} via Ollama.")
    print("Certifique-se que o serviço Ollama está rodando em segundo plano.")

    try:
        print("Inicializando componentes de IA (pode levar um momento)...")
        carregar_modelo_embedding()
        inicializar_chroma()
        print("Componentes de IA prontos.")
    except Exception as e:
        print(f"Erro fatal durante a inicialização: {e}")
        return

    while True:
        pergunta_usuario = input("\nQual sua pergunta sobre os documentos da família? (ou 'sair'): ")
        if pergunta_usuario.lower() in ['sair', 'exit', 'quit']:
            break
        if not pergunta_usuario.strip():
            continue

        # 1. Buscar chunks relevantes no ChromaDB
        chunks_relevantes = buscar_chunks_relevantes(pergunta_usuario, top_n=3)

        # 2. Formatar o prompt para o LLM
        prompt_para_llm = formatar_prompt(pergunta_usuario, chunks_relevantes)
        
        # 3. Gerar resposta com o LLM
        resposta_llm = gerar_resposta_com_llm(prompt_para_llm, nome_modelo_llm=MODELO_LLM_OLLAMA)

        print("\n" + "="*25 + " RESPOSTA DO ORÁCULO " + "="*25)
        print(resposta_llm)
        print("="*72)

        if chunks_relevantes:
            print("\n--- Documentos consultados para esta resposta: ---")
            for i, chunk_info in enumerate(chunks_relevantes):
                print(f"  Fonte {i+1}: Arquivo '{chunk_info['metadatos'].get('nome_arquivo_original', 'N/A')}'")
                # print(f"    (Distância: {chunk_info['distancia']:.4f})") # Descomente para depuração
                print(f"    Trecho Relevante: \"{chunk_info['texto_chunk'][:200]}...\"")
            print("-" * 52)
        else:
            print("\n(Nenhum trecho específico de documento foi considerado altamente relevante para esta pergunta)")
    
    print("\nOráculo Familiar encerrado. Até mais!")

if __name__ == "__main__":
    main()