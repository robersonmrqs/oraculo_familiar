# src/pdf_processor.py
import os
from pathlib import Path

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