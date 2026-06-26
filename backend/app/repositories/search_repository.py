"""Search data-access (FR-08).

Clause keyword search uses the MySQL FULLTEXT index on byelaw_clause.clause_text
(BOOLEAN MODE with prefix wildcards) for relevance ranking, with a LIKE fallback so
short tokens and clause titles (not in the FULLTEXT index) are still matched.
"""
from typing import Any, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _boolean_query(q: str) -> str:
    """Turn a user phrase into a BOOLEAN MODE query with prefix matching per term."""
    terms = [t for t in q.replace('"', " ").replace("*", " ").split() if t]
    return " ".join(f"+{t}*" for t in terms)


def _build_filters(registration_no, society_name, byelaw_title, chapter_no, active_only):
    clauses: list[str] = ["c.is_deleted = 0", "m.is_deleted = 0"]
    params: dict[str, Any] = {}
    if registration_no:
        clauses.append("LOWER(m.society_registration_no) = LOWER(:reg)")
        params["reg"] = registration_no
    if society_name:
        clauses.append("m.society_name LIKE :soc")
        params["soc"] = f"%{society_name}%"
    if byelaw_title:
        clauses.append("m.byelaw_title LIKE :title")
        params["title"] = f"%{byelaw_title}%"
    if chapter_no:
        clauses.append("c.chapter_no = :chapter")
        params["chapter"] = chapter_no
    if active_only:
        clauses.append("m.is_active = 1")
    return clauses, params


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
) -> tuple[Sequence[dict], int]:
    where, params = _build_filters(registration_no, society_name, byelaw_title, chapter_no, active_only)

    score_expr = "0"
    if q:
        bq = _boolean_query(q)
        if bq:  # at least one usable term
            params["bq"] = bq
            params["like"] = f"%{q}%"
            where.append(
                "(MATCH(c.clause_text) AGAINST (:bq IN BOOLEAN MODE) "
                "OR c.clause_text LIKE :like OR c.clause_title LIKE :like)"
            )
            score_expr = "MATCH(c.clause_text) AGAINST (:bq IN BOOLEAN MODE)"
        else:
            params["like"] = f"%{q}%"
            where.append("(c.clause_text LIKE :like OR c.clause_title LIKE :like)")

    where_sql = " AND ".join(where)

    count_sql = text(
        f"SELECT COUNT(*) FROM byelaw_clause c JOIN byelaw_master m "
        f"ON m.master_id = c.master_id WHERE {where_sql}"
    )
    total = (await db.execute(count_sql, params)).scalar_one()

    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size
    rows_sql = text(
        f"SELECT c.clause_id, c.master_id, c.parent_clause_id, c.clause_level, "
        f"c.chapter_no, c.clause_no, c.clause_title, c.clause_text, c.display_order, "
        f"m.society_name, m.society_registration_no, m.byelaw_title, m.byelaw_version, "
        f"m.is_active, ({score_expr}) AS score "
        f"FROM byelaw_clause c JOIN byelaw_master m ON m.master_id = c.master_id "
        f"WHERE {where_sql} "
        f"ORDER BY score DESC, c.master_id DESC, c.display_order ASC "
        f"LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(rows_sql, params)
    rows = [dict(r) for r in result.mappings().all()]
    return rows, total


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
) -> tuple[Sequence[dict], int]:
    """Bye-law metadata search; when q is given, also counts matching clauses per bye-law."""
    where: list[str] = ["m.is_deleted = 0"]
    params: dict[str, Any] = {}
    if registration_no:
        where.append("LOWER(m.society_registration_no) = LOWER(:reg)")
        params["reg"] = registration_no
    if society_name:
        where.append("m.society_name LIKE :soc")
        params["soc"] = f"%{society_name}%"
    if byelaw_title:
        where.append("m.byelaw_title LIKE :title")
        params["title"] = f"%{byelaw_title}%"
    if active_only:
        where.append("m.is_active = 1")

    match_count = "0"
    if q:
        bq = _boolean_query(q)
        params["like"] = f"%{q}%"
        if bq:
            params["bq"] = bq
            clause_cond = (
                "c.is_deleted = 0 AND (MATCH(c.clause_text) AGAINST (:bq IN BOOLEAN MODE) "
                "OR c.clause_text LIKE :like OR c.clause_title LIKE :like)"
            )
        else:
            clause_cond = "c.is_deleted = 0 AND (c.clause_text LIKE :like OR c.clause_title LIKE :like)"
        match_count = (
            f"(SELECT COUNT(*) FROM byelaw_clause c WHERE c.master_id = m.master_id AND {clause_cond})"
        )
        # Keep a bye-law in the results only if it has a matching clause OR its own
        # metadata matches the keyword — applied in WHERE so count and rows agree.
        where.append(
            f"(EXISTS (SELECT 1 FROM byelaw_clause c WHERE c.master_id = m.master_id AND {clause_cond}) "
            f"OR m.society_name LIKE :like OR m.byelaw_title LIKE :like "
            f"OR m.society_registration_no LIKE :like)"
        )

    where_sql = " AND ".join(where)

    count_sql = text(f"SELECT COUNT(*) FROM byelaw_master m WHERE {where_sql}")
    total = (await db.execute(count_sql, params)).scalar_one()

    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size
    rows_sql = text(
        f"SELECT m.master_id, m.society_name, m.society_registration_no, m.byelaw_title, "
        f"m.byelaw_version, m.is_active, m.extraction_status, m.workflow_status, "
        f"m.total_clauses, ({match_count}) AS match_count "
        f"FROM byelaw_master m WHERE {where_sql} "
        f"ORDER BY match_count DESC, m.master_id DESC "
        f"LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(rows_sql, params)
    rows = [dict(r) for r in result.mappings().all()]
    return rows, total
