# src/pdf_processor.py
"""
Módulo responsável por encontrar e processar arquivos PDF.
Extrai texto (usando OCR quando necessário) e calcula hashes de arquivos.
"""
import config
import hashlib
import ocrmypdf
import tempfile
from pathlib import Path
from PyPDF2 import PdfReader

def encontrar_pdfs(pasta_documentos: str) -> list[Path]:
    """
    Encontra todos os arquivos PDF em uma determinada pasta,
    independentemente do caso da extensão (.pdf ou .PDF).
    """
    caminho_pasta = Path(pasta_documentos)
    if not caminho_pasta.is_dir():
        print(f"Erro: A pasta '{pasta_documentos}' não foi encontrada.")
        return []

    arquivos_pdf_lower = list(caminho_pasta.glob("*.pdf"))
    arquivos_pdf_upper = list(caminho_pasta.glob("*.PDF"))
    
    # Retorna uma lista ordenada de caminhos únicos
    todos_os_pdfs_encontrados = sorted(list(set(arquivos_pdf_lower + arquivos_pdf_upper)))
    
    return todos_os_pdfs_encontrados

def calcular_hash_arquivo(caminho_arquivo: Path) -> str:
    """Calcula o hash SHA256 de um arquivo para detecção de duplicatas."""
    sha256_hash = hashlib.sha256()
    try:
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        print(f"Erro de I/O ao calcular hash para {caminho_arquivo.name}: {e}")
        return None

def extrair_texto_pdf(caminho_pdf: Path) -> str:
    """
    Extrai texto de um arquivo PDF, usando OCRmyPDF como fallback se necessário.
    Utiliza o limiar definido no arquivo de configuração.
    """
    texto_completo_buffer = ""
    try:
        leitor = PdfReader(caminho_pdf)
        for pagina in leitor.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto_completo_buffer += texto_pagina + "\n"
        
        texto_extraido_limpo = texto_completo_buffer.strip()
        
        # Usa o limiar do arquivo de configuração
        if len(texto_extraido_limpo) >= config.LIMIAR_MINIMO_TEXTO_OCR:
            return texto_extraido_limpo

        # Se o texto for insuficiente, tenta o OCR
        print(f"  - Texto direto insuficiente em '{caminho_pdf.name}'. Tentando OCR...")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_pdf_ocr:
            ocrmypdf.ocr(
                input_file=caminho_pdf,
                output_file=tmp_pdf_ocr.name,
                language='por', force_ocr=True, deskew=True, progress_bar=False
            )
            
            leitor_ocr = PdfReader(tmp_pdf_ocr.name)
            texto_ocr_buffer = "".join(page.extract_text() + "\n" for page in leitor_ocr.pages if page.extract_text())
            texto_ocr_limpo = texto_ocr_buffer.strip()
            
            return texto_ocr_limpo if texto_ocr_limpo else "AVISO: Nenhum texto extraído mesmo após OCR."

    except Exception as e:
        # Captura exceções de forma mais genérica para robustez
        print(f"  - ERRO Inesperado ao processar PDF '{caminho_pdf.name}': {e}")
        return f"ERRO: Falha ao processar o PDF {caminho_pdf.name}."