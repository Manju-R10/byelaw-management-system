/** Standard page header: title, optional subtitle and right-aligned actions. */
export default function PageHeader({ title, subtitle, icon, actions }) {
  return (
    <div className="section-head">
      <div className="d-flex align-items-center gap-3">
        {icon && (
          <div className="d-grid flex-shrink-0" style={{ width: 44, height: 44, placeItems: "center", borderRadius: 12, background: "#eef2ff", color: "#1e3a8a", fontSize: "1.3rem" }}>
            <i className={`bi ${icon}`} />
          </div>
        )}
        <div>
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="muted mb-0">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="d-flex gap-2 flex-wrap">{actions}</div>}
    </div>
  );
}
