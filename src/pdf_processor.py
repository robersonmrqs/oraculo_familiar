# src/pdf_processor.py
import os
from pathlib import Path
from PyPDF2 import PdfReader

def encontrar_pdfs(pasta_documentos: str) -> list[Path]:
    """Encontra todos os arquivos PDF em uma determinada pasta."""
    caminho_pasta = Path(pasta_documentos)
    if not caminho_pasta.is_dir():
        print(f"Erro: A pasta '{pasta_documentos}' não foi encontrada.")
        return []

    arquivos_pdf = list(caminho_pasta.glob("*.pdf"))
    print(f"Encontrados {len(arquivos_pdf)} arquivos PDF em '{pasta_documentos}'.")
    for pdf in arquivos_pdf:
        print(f" - {pdf.name}")
    return arquivos_pdf

def extrair_texto_pdf(caminho_pdf: Path) -> str:
    """
    Extrai texto de um arquivo PDF.
    Retorna as primeiras 500 caracteres como preview ou uma mensagem de erro.
    """
    try:
        leitor = PdfReader(caminho_pdf)
        texto_completo = ""
        for pagina in leitor.pages:
            texto_completo += pagina.extract_text() or ""

        if not texto_completo.strip():
            return "AVISO: Nenhum texto extraível encontrado (pode ser PDF de imagem)."
        return texto_completo[:500] + "..." # Retorna um preview
    except Exception as e:
        return f"ERRO ao extrair texto: {e}"