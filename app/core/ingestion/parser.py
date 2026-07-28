import os
from pathlib import Path

SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.csv', '.json', '.xml', '.html'}

def extract_text(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    if ext in ('.txt', '.md', '.csv', '.json', '.xml', '.html'):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == '.pdf':
        # Check if password protected
        try:
            import PyPDF2
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                if reader.is_encrypted:
                    raise ValueError("PDF is password protected. Cannot extract text.")
        except ImportError:
            pass
        except ValueError:
            raise

        # Try multiple PDF libraries
        text = ""
        libs = []

        # PyPDF2
        try:
            import PyPDF2
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            if text.strip():
                return text
            libs.append("PyPDF2 (0 chars)")
        except Exception as e:
            libs.append(f"PyPDF2: {e}")

        # pdfminer
        try:
            from pdfminer.high_level import extract_text as pdf_extract
            text = pdf_extract(filepath)
            if text.strip():
                return text
            libs.append("pdfminer (0 chars)")
        except Exception as e:
            libs.append(f"pdfminer: {e}")

        # pdfplumber
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            if text.strip():
                return text
            libs.append("pdfplumber (0 chars)")
        except Exception as e:
            libs.append(f"pdfplumber: {e}")

        raise ValueError(
            "Tidak bisa extract teks dari PDF ini.\n"
            "Kemungkinan: (1) PDF hasil scan/gambar tanpa teks, "
            "(2) PDF dilindungi password, "
            "(3) format PDF tidak didukung.\n"
            "Saran: upload file .txt atau .md sebagai alternatif."
        )
    raise ValueError(f'Unsupported file type: {ext}')
