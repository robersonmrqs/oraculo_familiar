# perguntar_oraculo.py
"""
Interface de Linha de Comando (CLI) para interagir com o Oráculo Familiar.
"""
import config
import sys
from src.ia_processor import inicializar_ia
from src.jarvis import Oraculo

def main_cli():
    """Loop principal para a interação via terminal."""
    print(f"Oráculo Familiar - {config.NOME_DO_BOT} - Interface de Linha de Comando")
    
    try:
        inicializar_ia()
    except Exception as e:
        print(f"\nErro fatal durante a inicialização: {e}")
        sys.exit(1)
        
    # Cria uma única instância do Oráculo para toda a sessão do terminal
    jarvis = Oraculo(nome_usuario="Você")

    while True:
        pergunta_usuario = input("\nSua pergunta: ")
        if pergunta_usuario.lower() in ['sair', 'exit', 'quit']:
            break
        if not pergunta_usuario.strip():
            continue

        # Verifica se é uma saudação ou despedida antes de chamar a IA
        palavras_da_mensagem = set(pergunta_usuario.lower().split())
        if any(saudacao in palavras_da_mensagem for saudacao in config.SAUDACOES):
            print(f"\n{config.NOME_DO_BOT}: Olá, {jarvis.nome_usuario}. Em que posso ser útil?")
            continue
        if len(palavras_da_mensagem) <= 3 and any(despedida in palavras_da_mensagem for despedida in config.DESPEDIDAS):
            print(f"\n{config.NOME_DO_BOT}: Entendido. Até mais!")
            break

        # Se for uma pergunta real, obtém a resposta do Oráculo
        resposta = jarvis.obter_resposta(pergunta_usuario)
        
        print("\n" + "="*25 + f" RESPOSTA DE {config.NOME_DO_BOT.upper()} " + "="*25)
        print(resposta)
        print("=" * (52 + len(config.NOME_DO_BOT)))

    print(f"\n{config.NOME_DO_BOT} encerrado.")


if __name__ == "__main__":
    main_cli()