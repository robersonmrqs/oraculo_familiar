# src/pdf_processor.py
import hashlib
import ocrmypdf
import os
import tempfile # Para criar arquivos/pastas temporárias
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
    
    todos_os_pdfs_encontrados = list(set(arquivos_pdf_lower + arquivos_pdf_upper))
    
    if todos_os_pdfs_encontrados:
        print(f"Encontrados {len(todos_os_pdfs_encontrados)} arquivos PDF (extensões .pdf ou .PDF) em '{pasta_documentos}':")
        for pdf_path in sorted(todos_os_pdfs_encontrados): # Ordenar para uma saída consistente
            print(f" - {pdf_path.name}")
    else:
        print(f"Nenhum arquivo com extensão .pdf ou .PDF encontrado em '{pasta_documentos}'.")
        
    return todos_os_pdfs_encontrados

def extrair_texto_pdf(caminho_pdf: Path, limiar_minimo_texto: int = 100) -> str:
    """
    Extrai texto de um arquivo PDF.
    Tenta primeiro com PyPDF2. Se o texto for insuficiente, usa OCRmyPDF.
    Retorna o TEXTO COMPLETO extraído ou uma mensagem de erro/aviso.
    """
    texto_completo_buffer = "" # Usar um buffer para acumular texto
    try:
        # Tentativa 1: Extração direta com PyPDF2
        leitor = PdfReader(caminho_pdf)
        for pagina in leitor.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto_completo_buffer += texto_pagina + "\n" # Adiciona uma nova linha entre páginas
        
        texto_extraido_limpo = texto_completo_buffer.strip()
        
        if len(texto_extraido_limpo) >= limiar_minimo_texto:
            print(f"Texto extraído diretamente de '{caminho_pdf.name}' (comprimento: {len(texto_extraido_limpo)}).")
            return texto_extraido_limpo # <<< RETORNA TEXTO COMPLETO

        # Tentativa 2: Usar OCRmyPDF se o texto direto for insuficiente
        print(f"Texto direto insuficiente em '{caminho_pdf.name}'. Tentando OCR...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho_pdf_ocr = Path(tmpdir) / f"{caminho_pdf.stem}_ocr.pdf"
            
            try:
                ocrmypdf.ocr(
                    input_file=caminho_pdf,
                    output_file=caminho_pdf_ocr,
                    language='por',
                    force_ocr=True,
                    skip_text=False,
                    deskew=True,
                )
                print(f"OCR completo para '{caminho_pdf.name}'. PDF com texto em: {caminho_pdf_ocr}")

                texto_ocr_buffer = "" # Buffer para texto do OCR
                leitor_ocr = PdfReader(caminho_pdf_ocr)
                for pagina_ocr in leitor_ocr.pages:
                    texto_pagina_ocr = pagina_ocr.extract_text()
                    if texto_pagina_ocr:
                        texto_ocr_buffer += texto_pagina_ocr + "\n" # Adiciona uma nova linha
                
                texto_ocr_limpo = texto_ocr_buffer.strip()

                if not texto_ocr_limpo:
                    return "AVISO: Nenhum texto extraído mesmo após OCR." # Mantém como está
                
                print(f"Texto extraído de '{caminho_pdf.name}' após OCR (comprimento: {len(texto_ocr_limpo)}).")
                return texto_ocr_limpo # <<< RETORNA TEXTO COMPLETO DO OCR

            except ocrmypdf.exceptions.MissingDependencyError:
                return "ERRO OCR: Alguma dependência do OCRmyPDF (como Tesseract) não está instalada corretamente."
            except ocrmypdf.exceptions.EncryptedPdfError:
                return f"ERRO OCR: O PDF '{caminho_pdf.name}' está criptografado."
            except Exception as e_ocr:
                return f"ERRO durante OCR em '{caminho_pdf.name}': {e_ocr}"

    except Exception as e_pypdf:
        return f"ERRO ao processar PDF '{caminho_pdf.name}' com PyPDF2: {e_pypdf}"
    
def calcular_hash_arquivo(caminho_arquivo: Path) -> str:
    """Calcula o hash SHA256 de um arquivo."""
    sha256_hash = hashlib.sha256()
    try:
        with open(caminho_arquivo, "rb") as f: # Abre o arquivo em modo binário para leitura
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Erro ao calcular hash para {caminho_arquivo.name}: {e}")
        return None