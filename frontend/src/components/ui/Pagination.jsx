/** Pagination bar with page buttons and a result summary. */
export default function Pagination({ page, totalPages, total, pageSize, onChange }) {
  if (total === 0) return null;

  const windowed = pageWindow(page, totalPages);
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="pagination-bar">
      <span className="muted">
        Showing <strong>{from}</strong>–<strong>{to}</strong> of <strong>{total}</strong>
      </span>
      <div className="pages">
        <button className="page-btn" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Previous page">
          <i className="bi bi-chevron-left" />
        </button>
        {windowed.map((p, i) =>
          p === "…" ? (
            <span key={`g${i}`} className="page-btn" style={{ border: "none", cursor: "default" }}>…</span>
          ) : (
            <button key={p} className={`page-btn ${p === page ? "active" : ""}`} onClick={() => onChange(p)} aria-current={p === page ? "page" : undefined}>
              {p}
            </button>
          )
        )}
        <button className="page-btn" disabled={page >= totalPages} onClick={() => onChange(page + 1)} aria-label="Next page">
          <i className="bi bi-chevron-right" />
        </button>
      </div>
    </div>
  );
}

function pageWindow(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = new Set([1, total, current, current - 1, current + 1]);
  const sorted = [...pages].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b);
  const out = [];
  let prev = 0;
  for (const p of sorted) {
    if (p - prev > 1) out.push("…");
    out.push(p);
    prev = p;
  }
  return out;
}
