"""End-to-end fact-check pipeline orchestration."""

from __future__ import annotations

from typing import Any, Callable

from services.claim_extractor import ClaimExtractor
from services.pdf_parser import PDFParser
from services.verifier import Verifier
from utils.helpers import validate_pdf_file

ProgressCallback = Callable[[str, int], None]


class FactCheckPipeline:
    """Run PDF extraction, claim detection, and verification as one workflow."""

    def __init__(self, model: str):
        self.model = model
        self.parser = PDFParser()
        self.extractor = ClaimExtractor(model=model)
        self.verifier = Verifier(model=model)

    def run(
        self,
        uploaded_file,
        *,
        remove_duplicates: bool = True,
        max_claims: int = 40,
        min_confidence: int = 0,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        is_valid, error = validate_pdf_file(uploaded_file)
        if not is_valid:
            return {}, error or "Invalid PDF file."

        def notify(message: str, percent: int) -> None:
            if progress_callback:
                progress_callback(message, percent)

        notify("Reading PDF...", 10)
        text, pdf_error = self.parser.extract_text(uploaded_file)
        if pdf_error:
            return {}, pdf_error

        metadata = self.parser.get_pdf_metadata(uploaded_file)
        notify("Extracting factual claims...", 35)
        claims, claim_error = self.extractor.extract_and_process_claims(
            text,
            remove_duplicates=remove_duplicates,
            max_claims=max_claims,
        )
        if claim_error:
            return {}, claim_error
        if not claims:
            return {}, "No verifiable claims were found in this document."

        notify("Searching evidence and verifying claims...", 55)

        def verify_progress(current: int, total: int) -> None:
            base = 55 + int((current / max(total, 1)) * 40)
            notify(f"Verified {current} of {total} claims", base)

        results, verify_error = self.verifier.verify_claims(
            claims,
            progress_callback=verify_progress,
            min_confidence=min_confidence,
        )
        if verify_error:
            return {}, verify_error

        notify("Pipeline complete", 100)
        return {
            "extracted_text": text,
            "extracted_claims": claims,
            "verification_results": results,
            "document_metadata": metadata,
            "document_name": uploaded_file.name,
        }, None
