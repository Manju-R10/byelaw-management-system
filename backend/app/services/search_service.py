"""Search service (FR-08): clause keyword search and bye-law metadata search.

Produces a contextual snippet for each clause hit so matches are shown "in context"
as required by FR-08, with the matched terms returned for client-side highlighting.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import search_repository
from app.schemas.common import PaginatedResponse
from app.schemas.search import ByelawSearchHit, ClauseSearchHit

_SNIPPET_RADIUS = 120  # characters of context on each side of the first match


def _terms(q: Optional[str]) -> List[str]:
    if not q:
        return []
    return [t for t in q.replace('"', " ").split() if t]


def _make_snippet(text: str, terms: List[str]) -> str:
    """Return a context window around the first matching term, else the head of the text."""
    if not text:
        return ""
    lowered = text.lower()
    first_pos = -1
    for term in terms:
        pos = lowered.find(term.lower())
        if pos != -1 and (first_pos == -1 or pos < first_pos):
            first_pos = pos
    if first_pos == -1:
        snippet = text[: _SNIPPET_RADIUS * 2].strip()
        return snippet + ("…" if len(text) > _SNIPPET_RADIUS * 2 else "")
    start = max(0, first_pos - _SNIPPET_RADIUS)
    end = min(len(text), first_pos + _SNIPPET_RADIUS)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


async def search_clauses(
    db: AsyncSession,
    *,
    q: Optional[str],
    registration_no: Optional[str],
    society_name: Optional[str],
    byelaw_title: Optional[str],
    chapter_no: Optional[str],
    active_only: bool,
    page: int,
    page_size: int,
) -> PaginatedResponse[ClauseSearchHit]:
    rows, total = await search_repository.search_clauses(
        db, q=q, registration_no=registration_no, society_name=society_name,
        byelaw_title=byelaw_title, chapter_no=chapter_no, active_only=active_only,
        page=page, page_size=page_size,
    )
    terms = _terms(q)
    items = [
        ClauseSearchHit(
            clause_id=r["clause_id"],
            master_id=r["master_id"],
            parent_clause_id=r["parent_clause_id"],
            clause_level=r["clause_level"],
            chapter_no=r["chapter_no"],
            clause_no=r["clause_no"],
            clause_title=r["clause_title"],
            snippet=_make_snippet(r["clause_text"], terms),
            display_order=r["display_order"],
            score=float(r["score"]) if r["score"] is not None else 0.0,
            society_name=r["society_name"],
            society_registration_no=r["society_registration_no"],
            byelaw_title=r["byelaw_title"],
            byelaw_version=r["byelaw_version"],
            is_active=bool(r["is_active"]),
            matched_terms=terms,
        )
        for r in rows
    ]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


async def search_byelaws(
    db: AsyncSession,
    *,
    q: Optional[str],
    registration_no: Optional[str],
    society_name: Optional[str],
    byelaw_title: Optional[str],
    active_only: bool,
    page: int,
    page_size: int,
) -> PaginatedResponse[ByelawSearchHit]:
    rows, total = await search_repository.search_byelaws(
        db, q=q, registration_no=registration_no, society_name=society_name,
        byelaw_title=byelaw_title, active_only=active_only, page=page, page_size=page_size,
    )
    items = [
        ByelawSearchHit(
            master_id=r["master_id"],
            society_name=r["society_name"],
            society_registration_no=r["society_registration_no"],
            byelaw_title=r["byelaw_title"],
            byelaw_version=r["byelaw_version"],
            is_active=bool(r["is_active"]),
            extraction_status=r["extraction_status"],
            workflow_status=r["workflow_status"],
            total_clauses=r["total_clauses"],
            match_count=int(r["match_count"]) if r["match_count"] is not None else 0,
        )
        for r in rows
    ]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
