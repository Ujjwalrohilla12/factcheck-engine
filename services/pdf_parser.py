"""PDF parsing service with multiple extraction backends."""

from __future__ import annotations

import io

import fitz
import pdfplumber

from utils.constants import ERROR_INVALID_PDF
from utils.helpers import sanitize_text


class PDFParser:
    """Extract text and metadata from uploaded PDF files."""

    @staticmethod
    def extract_text(pdf_file) -> tuple[str, str | None]:
        """Extract text from a PDF using pdfplumber with PyMuPDF fallback."""
        try:
            pdf_bytes = pdf_file.read()
            pdf_file.seek(0)

            text = PDFParser._extract_with_pdfplumber(pdf_bytes)
            if len(text.strip()) < 50:
                text = PDFParser._extract_with_pymupdf(pdf_bytes)

            text = sanitize_text(text)
            if len(text) < 50:
                return "", ERROR_INVALID_PDF

            return text, None
        except Exception as exc:
            return "", f"PDF parsing error: {exc}"

    @staticmethod
    def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
        text_parts: list[str] = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                    if page_text.strip():
                        text_parts.append(f"\n\n--- Page {index} ---\n{page_text}")
        except Exception:
            return ""
        return "\n".join(text_parts)

    @staticmethod
    def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
        text_parts: list[str] = []
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                for index, page in enumerate(document, start=1):
                    page_text = page.get_text("text") or ""
                    if page_text.strip():
                        text_parts.append(f"\n\n--- Page {index} ---\n{page_text}")
        except Exception:
            return ""
        return "\n".join(text_parts)

    @staticmethod
    def get_pdf_metadata(pdf_file) -> dict:
        """Return basic metadata for display."""
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)

        metadata = {"pages": 0, "file_size_mb": len(pdf_bytes) / (1024 * 1024)}
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
                metadata["pages"] = document.page_count
                metadata["title"] = document.metadata.get("title") or pdf_file.name
        except Exception as exc:
            metadata["error"] = str(exc)
        return metadata
