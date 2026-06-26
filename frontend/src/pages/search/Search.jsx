import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { searchApi } from "../../api/search";
import { getApiError } from "../../api/client";
import { useDebounce } from "../../hooks/useDebounce";
import PageHeader from "../../components/ui/PageHeader";
import Pagination from "../../components/ui/Pagination";
import StatusBadge from "../../components/ui/StatusBadge";
import EmptyState from "../../components/ui/EmptyState";
import Highlight from "../../components/ui/Highlight";
import { SkeletonLines } from "../../components/ui/Skeleton";

const HISTORY_KEY = "blms_search_history";

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; } catch { return []; }
}

export default function Search() {
  const [mode, setMode] = useState("clauses"); // "clauses" | "byelaws"
  const [q, setQ] = useState("");
  const debouncedQ = useDebounce(q, 400);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ registration_no: "", society_name: "", byelaw_title: "", chapter_no: "", active_only: false });
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [data, setData] = useState({ items: [], total: 0, total_pages: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);
  const [history, setHistory] = useState(loadHistory);
  const savedRef = useRef("");

  const run = useCallback(async () => {
    const hasQuery = debouncedQ.trim() || Object.values(filters).some((v) => v !== "" && v !== false);
    if (!hasQuery) { setData({ items: [], total: 0, total_pages: 0 }); setSearched(false); return; }
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const params = { page, page_size: pageSize };
      if (debouncedQ.trim()) params.q = debouncedQ.trim();
      Object.entries(filters).forEach(([k, v]) => { if (v !== "" && v !== false) params[k] = v; });
      if (mode === "byelaws") delete params.chapter_no;
      const res = mode === "clauses" ? await searchApi.clauses(params) : await searchApi.byelaws(params);
      setData(res.data);
      // record history once per distinct query
      if (debouncedQ.trim() && savedRef.current !== debouncedQ.trim()) {
        savedRef.current = debouncedQ.trim();
        setHistory((prev) => {
          const next = [debouncedQ.trim(), ...prev.filter((h) => h !== debouncedQ.trim())].slice(0, 8);
          localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
          return next;
        });
      }
    } catch (err) {
      setError(getApiError(err));
      setData({ items: [], total: 0, total_pages: 0 });
    } finally {
      setLoading(false);
    }
  }, [debouncedQ, filters, page, mode]);

  useEffect(() => { run(); }, [run]);
  useEffect(() => { setPage(1); }, [debouncedQ, mode, filters]);

  const setFilter = (k, v) => setFilters((f) => ({ ...f, [k]: v }));
  const clearAll = () => { setQ(""); setFilters({ registration_no: "", society_name: "", byelaw_title: "", chapter_no: "", active_only: false }); };
  const terms = debouncedQ.trim() ? debouncedQ.trim().split(/\s+/) : [];

  return (
    <div>
      <PageHeader title="Search" subtitle="Find bye-laws and clauses by keyword, society or chapter." icon="bi-search" />

      <div className="app-card p-3 mb-3">
        <div className="d-flex gap-2 flex-wrap align-items-center">
          <div className="search-box flex-grow-1" style={{ position: "relative", minWidth: 240 }}>
            <i className="bi bi-search" style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "#94a3b8" }} />
            <input className="form-control" style={{ paddingLeft: "2.2rem" }} placeholder={mode === "clauses" ? "Search clause text…" : "Search bye-laws…"} value={q} onChange={(e) => setQ(e.target.value)} autoFocus />
          </div>
          <div className="btn-group">
            <button className={`btn ${mode === "clauses" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => setMode("clauses")}><i className="bi bi-list-nested me-1" />Clauses</button>
            <button className={`btn ${mode === "byelaws" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => setMode("byelaws")}><i className="bi bi-journal-text me-1" />Bye-laws</button>
          </div>
          <button className="btn btn-light" onClick={() => setShowFilters((v) => !v)}><i className="bi bi-funnel me-1" />Filters</button>
        </div>

        {showFilters && (
          <div className="row g-2 mt-2 fade-in">
            <div className="col-12 col-md-3"><input className="form-control" placeholder="Registration no." value={filters.registration_no} onChange={(e) => setFilter("registration_no", e.target.value)} /></div>
            <div className="col-12 col-md-3"><input className="form-control" placeholder="Society name" value={filters.society_name} onChange={(e) => setFilter("society_name", e.target.value)} /></div>
            <div className="col-12 col-md-3"><input className="form-control" placeholder="Bye-law title" value={filters.byelaw_title} onChange={(e) => setFilter("byelaw_title", e.target.value)} /></div>
            {mode === "clauses" && <div className="col-6 col-md-2"><input className="form-control" placeholder="Chapter no." value={filters.chapter_no} onChange={(e) => setFilter("chapter_no", e.target.value)} /></div>}
            <div className="col-6 col-md-1 d-flex align-items-center">
              <div className="form-check form-switch">
                <input className="form-check-input" type="checkbox" id="active-only" checked={filters.active_only} onChange={(e) => setFilter("active_only", e.target.checked)} />
                <label className="form-check-label small" htmlFor="active-only">Active</label>
              </div>
            </div>
          </div>
        )}

        {history.length > 0 && (
          <div className="d-flex align-items-center gap-2 mt-2 flex-wrap">
            <span className="text-muted small"><i className="bi bi-clock-history me-1" />Recent:</span>
            {history.map((h) => <span key={h} className="filter-chip cursor-pointer" onClick={() => setQ(h)}>{h}</span>)}
            <button className="btn btn-sm btn-link text-decoration-none p-0 text-muted" onClick={clearAll}>Clear</button>
          </div>
        )}
      </div>

      {/* Results */}
      {loading ? (
        <div className="app-card p-3"><SkeletonLines rows={5} /></div>
      ) : error ? (
        <div className="app-card"><EmptyState icon="bi-exclamation-octagon" title="Search failed" subtitle={error} /></div>
      ) : !searched ? (
        <div className="app-card"><EmptyState icon="bi-search" title="Start typing to search" subtitle="Search clause text, or switch to bye-law search." /></div>
      ) : data.items.length === 0 ? (
        <div className="app-card"><EmptyState icon="bi-emoji-neutral" title="No results found" subtitle="Try a different keyword or adjust your filters." /></div>
      ) : (
        <>
          <div className="text-muted small mb-2">{data.total} result{data.total !== 1 ? "s" : ""}</div>
          {mode === "clauses" ? (
            <div className="d-flex flex-column gap-2">
              {data.items.map((hit) => (
                <Link key={hit.clause_id} to={`/byelaws/${hit.master_id}`} className="app-card hoverable p-3 text-decoration-none text-body">
                  <div className="d-flex justify-content-between align-items-start gap-2 flex-wrap">
                    <div className="d-flex align-items-center gap-2">
                      {(hit.chapter_no || hit.clause_no) && <span className="clause-no-pill">{hit.chapter_no || hit.clause_no}</span>}
                      <span className="fw-semibold">{hit.clause_title || "Clause"}</span>
                    </div>
                    {hit.is_active && <span className="status-badge" style={{ background: "#d1fae5", color: "#047857" }}><span className="dot" />Active</span>}
                  </div>
                  <div className="mt-1" style={{ color: "#334155" }}><Highlight text={hit.snippet} terms={terms} /></div>
                  <div className="text-muted small mt-2"><i className="bi bi-journal-text me-1" />{hit.society_name} · {hit.byelaw_title} · v{hit.byelaw_version}</div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="d-flex flex-column gap-2">
              {data.items.map((b) => (
                <Link key={b.master_id} to={`/byelaws/${b.master_id}`} className="app-card hoverable p-3 text-decoration-none text-body d-flex justify-content-between align-items-center gap-3 flex-wrap">
                  <div>
                    <div className="fw-semibold">{b.society_name} <span className="text-muted">· {b.society_registration_no}</span></div>
                    <div className="text-muted small">{b.byelaw_title} · v{b.byelaw_version}</div>
                  </div>
                  <div className="d-flex align-items-center gap-3">
                    {b.match_count > 0 && <span className="filter-chip">{b.match_count} match{b.match_count !== 1 ? "es" : ""}</span>}
                    <StatusBadge status={b.workflow_status} />
                    {b.is_active && <span className="status-badge" style={{ background: "#d1fae5", color: "#047857" }}><span className="dot" />Active</span>}
                    <i className="bi bi-chevron-right text-muted" />
                  </div>
                </Link>
              ))}
            </div>
          )}

          <div className="app-card mt-2">
            <Pagination page={page} totalPages={data.total_pages} total={data.total} pageSize={pageSize} onChange={setPage} />
          </div>
        </>
      )}
    </div>
  );
}
