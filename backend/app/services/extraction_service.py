"""Extraction Engine: parse a document into a clause hierarchy and persist it.

Implements FR-04 (data extraction), FR-05 (hierarchy construction with anomaly
flagging) and FR-06 (transactional persistence of Head + Child clauses). The engine
is intentionally independent of the web layer so it could later run asynchronously
for large documents (FRS Section 5.2).
"""
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.extraction_rules import (
    LEVEL_CHAPTER,
    ClassifiedHeading,
    RuleSet,
    get_default_ruleset,
)
from app.core.logging_config import get_logger
from app.models.byelaw import ByelawClause, ByelawMaster
from app.repositories import clause_repository

logger = get_logger(__name__)

# Schemes whose trailing text is a heading *title*; for the rest (letter/paren
# markers) the trailing text is the first line of the clause *body*.
_TITLE_SCHEMES = {"numeric", "dotted_numeric", "roman_chapter", "byelaw_no", "rule_paren", "docx_style"}


@dataclass
class ParsedNode:
    level: int
    number: str
    title: Optional[str]
    scheme: str
    body_lines: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        body = "\n".join(line for line in self.body_lines if line).strip()
        if body:
            return body
        # A heading with no body still needs non-null clause_text.
        return (self.title or self.number or "").strip()


@dataclass
class _Line:
    text: str
    style_level: Optional[int] = None  # set when a DOCX paragraph uses a Heading style


# --------------------------------------------------------------------------------------
# Document readers (FR-04)
# --------------------------------------------------------------------------------------

def _docx_lines(path: str) -> List[_Line]:
    import docx

    document = docx.Document(path)
    lines: List[_Line] = []
    for para in document.paragraphs:
        text = (para.text or "").strip()
        if not text:
            continue
        style_level: Optional[int] = None
        style_name = (para.style.name if para.style else "") or ""
        if style_name.lower().startswith("heading"):
            digits = "".join(ch for ch in style_name if ch.isdigit())
            if digits:
                style_level = min(int(digits), 4)
        lines.append(_Line(text=text, style_level=style_level))
    return lines


def _pdf_lines(path: str) -> List[_Line]:
    import pdfplumber

    lines: List[_Line] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw in text.splitlines():
                stripped = raw.strip()
                if stripped:
                    lines.append(_Line(text=stripped))
    return lines


def read_document_lines(path: str, file_type: str) -> List[_Line]:
    file_type = file_type.upper()
    if file_type == "DOCX":
        return _docx_lines(path)
    if file_type in ("PDF", "DOC"):
        # Legacy .doc is read via the PDF/text path only if it yields text; otherwise
        # the caller will receive an empty list and surface a clear message.
        if file_type == "PDF":
            return _pdf_lines(path)
        return _doc_lines(path)
    raise ValueError(f"Unsupported file type for extraction: {file_type}")


def _doc_lines(path: str) -> List[_Line]:
    # Best-effort plain-text read for legacy binary .doc; structured parsing of .doc
    # is out of scope (FRS focuses on DOCX/PDF). Returns empty if not decodable.
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8", errors="ignore")
        return [_Line(text=ln.strip()) for ln in text.splitlines() if ln.strip()]
    except OSError:
        return []


# --------------------------------------------------------------------------------------
# Classification + node building (FR-04)
# --------------------------------------------------------------------------------------

def _classify(line: _Line, ruleset: RuleSet) -> Optional[ClassifiedHeading]:
    if line.style_level is not None:
        # DOCX heading style is authoritative for the level; still try to mine a
        # number/title from the text via the ruleset.
        mined = ruleset.classify(line.text)
        number = mined.number if mined else ""
        title = mined.title if (mined and mined.title) else line.text
        return ClassifiedHeading(level=line.style_level, number=number, title=title, scheme="docx_style")
    return ruleset.classify(line.text)


def build_nodes(lines: List[_Line], ruleset: RuleSet) -> List[ParsedNode]:
    nodes: List[ParsedNode] = []
    current: Optional[ParsedNode] = None

    for line in lines:
        heading = _classify(line, ruleset)
        if heading is not None:
            if heading.scheme in _TITLE_SCHEMES:
                title = heading.title or None
                body: List[str] = []
            else:
                # Letter/paren markers: trailing text is the start of the body.
                title = None
                body = [heading.title] if heading.title else []
            node = ParsedNode(
                level=heading.level, number=heading.number, title=title,
                scheme=heading.scheme, body_lines=body,
            )
            nodes.append(node)
            current = node
        else:
            if current is None:
                # Text before any recognized heading becomes a Preamble chapter.
                current = ParsedNode(level=LEVEL_CHAPTER, number="", title="Preamble", scheme="preamble")
                nodes.append(current)
            current.body_lines.append(line.text)

    return nodes


# --------------------------------------------------------------------------------------
# Hierarchy validation (FR-05)
# --------------------------------------------------------------------------------------

def detect_warnings(nodes: List[ParsedNode]) -> List[str]:
    """Flag numbering anomalies for the reviewer (never silently corrected — FR-05)."""
    warnings: List[str] = []
    prev_level = 0
    last_numeric_by_level: dict[int, int] = {}

    for idx, node in enumerate(nodes, start=1):
        # Level jumps by more than one (e.g. chapter directly to sub-clause).
        if node.level > prev_level + 1 and prev_level != 0:
            warnings.append(
                f"Node {idx} ('{node.number or node.title or ''}'): level jumps from "
                f"{prev_level} to {node.level} (possible missing intermediate heading)."
            )
        # Out-of-sequence simple numeric siblings.
        if node.number.isdigit():
            n = int(node.number)
            last = last_numeric_by_level.get(node.level)
            if last is not None and n != last + 1:
                warnings.append(
                    f"Node {idx}: numbering '{node.number}' is out of sequence "
                    f"(previous sibling at this level was {last})."
                )
            last_numeric_by_level[node.level] = n
            # Reset deeper levels when a new higher-level number starts.
            for lvl in list(last_numeric_by_level):
                if lvl > node.level:
                    del last_numeric_by_level[lvl]
        prev_level = node.level

    return warnings


# --------------------------------------------------------------------------------------
# Persistence (FR-06)
# --------------------------------------------------------------------------------------

def parse_document(
    path: str, file_type: str, ruleset: Optional[RuleSet] = None
) -> Tuple[List[ParsedNode], List[str]]:
    """Pure (no-DB) parse: read the file, classify, build nodes and detect anomalies.

    This is CPU/IO-bound and synchronous; callers run it in a worker thread so the
    async event loop (and its DB connections) are never blocked during a large parse.
    """
    ruleset = ruleset or get_default_ruleset()
    lines = read_document_lines(path, file_type)
    nodes = build_nodes(lines, ruleset)
    warnings = detect_warnings(nodes)
    return nodes, warnings


async def extract_and_persist(
    db: AsyncSession,
    master: ByelawMaster,
    actor_id: int,
    ruleset: Optional[RuleSet] = None,
) -> Tuple[int, int, List[str]]:
    """Parse the master's source file and persist its clause tree in one transaction.

    Returns (total_clauses, total_chapters, warnings). Raises on read/DB failure
    after rolling back so the bye-law is never left partially stored.
    """
    # Run the blocking parse off the event loop (FRS: Extraction Engine kept
    # independent of the web layer and separable into an async worker).
    nodes, warnings = await asyncio.to_thread(
        parse_document, master.source_file_path, master.source_file_type, ruleset
    )

    if not nodes:
        raise ValueError("No extractable text/clauses were found in the document.")

    try:
        # Re-extraction replaces any previously extracted clauses for this bye-law.
        await clause_repository.delete_by_master(db, master.master_id)

        stack: List[Tuple[int, int]] = []  # (level, clause_id)
        display_order = 0
        chapter_count = 0

        for node in nodes:
            display_order += 1
            while stack and stack[-1][0] >= node.level:
                stack.pop()
            parent_id = stack[-1][1] if stack else None

            clause = ByelawClause(
                master_id=master.master_id,
                parent_clause_id=parent_id,
                clause_level=node.level,
                chapter_no=node.number if node.level == LEVEL_CHAPTER else None,
                clause_no=node.number or None,
                clause_title=(node.title[:255] if node.title else None),
                clause_text=node.text or (node.number or "(no text)"),
                display_order=display_order,
                created_by=actor_id,
                updated_by=actor_id,
            )
            db.add(clause)
            await db.flush()  # obtain clause_id for child linking
            stack.append((node.level, clause.clause_id))
            if node.level == LEVEL_CHAPTER:
                chapter_count += 1

        master.total_clauses = len(nodes)
        master.total_chapters = chapter_count
        master.extraction_status = "Completed"
        master.updated_by = actor_id

        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Clause persistence failed for master_id=%s; rolled back.", master.master_id)
        raise

    logger.info(
        "Extraction complete: master_id=%s clauses=%s chapters=%s warnings=%s",
        master.master_id, len(nodes), chapter_count, len(warnings),
    )
    return len(nodes), chapter_count, warnings
