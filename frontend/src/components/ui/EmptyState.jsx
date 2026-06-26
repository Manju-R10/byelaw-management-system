/** Friendly empty-state placeholder for lists/tables with no data. */
export default function EmptyState({ icon = "bi-inbox", title = "Nothing here yet", subtitle, className = "" }) {
  return (
    <div className={`text-center py-4 px-3 ${className}`}>
      <div
        className="mx-auto mb-2 d-grid"
        style={{
          width: 56, height: 56, placeItems: "center", borderRadius: 14,
          background: "#f1f5f9", color: "#94a3b8", fontSize: "1.5rem",
        }}
      >
        <i className={`bi ${icon}`} />
      </div>
      <div className="fw-semibold text-strong">{title}</div>
      {subtitle && <div className="muted small mt-1">{subtitle}</div>}
    </div>
  );
}
