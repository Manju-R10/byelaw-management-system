"""Document readability validation (FR-03).

Attempts to open a stored upload with the appropriate library and reports whether
it is readable, without ever crashing the upload workflow. Parsing/extraction of
the clause hierarchy is a separate concern handled by the Extraction Engine (M5).
"""
from dataclasses import dataclass
from pathlib import Path

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# OLE2 compound-document magic number used by legacy .doc (and other MS formats).
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


@dataclass
class ValidationResult:
    is_valid: bool
    message: str
    page_or_paragraph_count: int = 0


def _validate_pdf(path: str) -> ValidationResult:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        if page_count == 0:
            return ValidationResult(False, "PDF contains no pages.", 0)
        # Touch the first page to confirm the content stream is parseable.
        _ = pdf.pages[0].extract_text()
    return ValidationResult(True, f"PDF is readable ({page_count} page(s)).", page_count)


def _validate_docx(path: str) -> ValidationResult:
    import docx

    document = docx.Document(path)
    paragraph_count = len(document.paragraphs)
    if paragraph_count == 0:
        return ValidationResult(False, "DOCX contains no paragraphs.", 0)
    return ValidationResult(True, f"DOCX is readable ({paragraph_count} paragraph(s)).", paragraph_count)


def _validate_doc(path: str) -> ValidationResult:
    # Legacy binary .doc cannot be parsed by python-docx; verify the OLE2 signature
    # so we at least confirm the file is a genuine Word binary document.
    with open(path, "rb") as fh:
        header = fh.read(8)
    if header != _OLE_MAGIC:
        return ValidationResult(False, "File does not appear to be a valid Word (.doc) document.", 0)
    return ValidationResult(True, "Legacy .doc document accepted (structure parsed during review).", 0)


def validate_document(path: str, file_type: str) -> ValidationResult:
    """Validate a stored document by type. Never raises — failures are returned as results."""
    if not Path(path).exists():
        return ValidationResult(False, "Stored file could not be located on the server.")

    file_type = file_type.upper()
    try:
        if file_type == "PDF":
            return _validate_pdf(path)
        if file_type == "DOCX":
            return _validate_docx(path)
        if file_type == "DOC":
            return _validate_doc(path)
        return ValidationResult(False, f"Unsupported file type '{file_type}'.")
    except Exception as exc:  # noqa: BLE001 — any parse error means the file is unreadable
        logger.warning("Document validation failed for %s (%s): %s", path, file_type, exc)
        return ValidationResult(False, f"Failed - Unreadable File: {exc}")
