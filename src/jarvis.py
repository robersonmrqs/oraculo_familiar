# src/jarvis.py
"""
Contém a classe principal 'Oraculo', que encapsula a lógica de conversação,
buscando contexto e interagindo com o LLM para gerar respostas.
"""
import config
from .ia_processor import buscar_chunks_relevantes, gerar_resposta_com_llm

class Oraculo:
    """
    Representa uma sessão de conversa com o Jarvis.
    Gerencia o histórico e o fluxo de pergunta e resposta.
    """
    def __init__(self, nome_usuario: str = "Usuário"):
        self.nome_usuario = nome_usuario
        self.historico_conversa = []
        print(f"Nova sessão do Oráculo iniciada para {self.nome_usuario}.")

    def _formatar_prompt(self, pergunta_usuario: str, chunks_contexto: list[dict]) -> str:
        """
        Formata o prompt para o LLM com o histórico, a pergunta e o contexto.
        Este é um método "privado" da classe.
        """
        historico_formatado = ""
        if self.historico_conversa:
            historico_formatado += "--- INÍCIO DO HISTÓRICO DA CONVERSA ---\n"
            for turno in self.historico_conversa:
                role = self.nome_usuario if turno["role"] == "user" else config.NOME_DO_BOT
                historico_formatado += f"{role}: {turno['content']}\n"
            historico_formatado += "--- FIM DO HISTÓRICO DA CONVERSA ---\n\n"

        contexto_str = "\n\n---\n\n".join([chunk.get('texto_chunk', '') for chunk in chunks_contexto])

        instrucao_sistema = (
            f"Você é {config.NOME_DO_BOT}, um assistente de IA prestativo e espirituoso do 'Oráculo Familiar'. "
            "Sua tarefa é responder a NOVA PERGUNTA do usuário baseando-se estritamente no CONTEXTO (extraído de documentos familiares) "
            "e no HISTÓRICO DA CONVERSA, se for relevante.\n"
            "Se a informação não estiver no CONTEXTO, diga 'Com base nos documentos disponíveis, não possuo dados sobre isso.'. "
            "Mantenha um tom profissional, mas com um toque sutil de sagacidade.\n\n"
        )
        
        if not chunks_contexto:
             instrucao_sistema += "Nenhum documento relevante foi encontrado para a pergunta atual.\n\n"

        prompt = (
            instrucao_sistema +
            historico_formatado +
            f"CONTEXTO ATUAL (DOCUMENTOS RELEVANTES PARA A NOVA PERGUNTA):\n{contexto_str}\n\n"
            f"NOVA PERGUNTA: {pergunta_usuario}\n\n"
            "RESPOSTA:"
        )
        return prompt

    def obter_resposta(self, pergunta_usuario: str) -> str:
        """
        Processa uma nova pergunta, executa todo o pipeline RAG e retorna a resposta.
        """
        print(f"Processando pergunta de {self.nome_usuario}: '{pergunta_usuario}'")
        
        # 1. Buscar chunks relevantes
        chunks_relevantes = buscar_chunks_relevantes(pergunta_usuario, top_n=config.TOP_N_CHUNKS)

        # 2. Formatar o prompt
        prompt_para_llm = self._formatar_prompt(pergunta_usuario, chunks_relevantes)
        
        # 3. Gerar resposta com o LLM
        resposta_llm = gerar_resposta_com_llm(prompt_para_llm, nome_modelo_llm=config.MODELO_LLM_OLLAMA)
        
        # 4. Atualizar o histórico da sessão
        self.historico_conversa.append({"role": "user", "content": pergunta_usuario})
        self.historico_conversa.append({"role": "assistant", "content": resposta_llm})

        return resposta_llm