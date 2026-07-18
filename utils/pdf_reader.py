from __future__ import annotations
import re
import pdfplumber
from io import BytesIO
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    text: str
    success: bool
    page_count: int
    warning: str | None = None


def _clean_whitespace(text: str) -> str:
    text = re.sub(r"\t", " ", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(uploaded_file) -> ExtractionResult:
    if uploaded_file is None:
        return ExtractionResult(text="", success=False, page_count=0, warning="No file provided.")

    try:
        pdf_bytes = BytesIO(uploaded_file.read())
        page_count = 0
        full_text = ""

        with pdfplumber.open(pdf_bytes) as pdf:
            page_count = len(pdf.pages)
            if page_count == 0:
                return ExtractionResult(
                    text="", success=False, page_count=0, warning="PDF contains no pages."
                )
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

        full_text = _clean_whitespace(full_text)

        if not full_text:
            return ExtractionResult(
                text="",
                success=False,
                page_count=page_count,
                warning="No extractable text found. The PDF may be scanned or image-based.",
            )

        if len(full_text) < 50:
            return ExtractionResult(
                text=full_text,
                success=False,
                page_count=page_count,
                warning=f"Very little text extracted ({len(full_text)} chars). The PDF may be scanned or corrupted.",
            )

        return ExtractionResult(text=full_text, success=True, page_count=page_count)

    except Exception as e:
        return ExtractionResult(
            text="", success=False, page_count=0, warning=f"PDF extraction failed: {e}"
        )
