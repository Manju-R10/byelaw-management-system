/** Colored status pill for extraction_status and workflow_status values. */
const STATUS_STYLES = {
  // Workflow statuses
  Draft: { bg: "#eef2f7", fg: "#475569" },
  Submitted: { bg: "#e0edff", fg: "#1d4ed8" },
  "Under Review": { bg: "#fff4e0", fg: "#b45309" },
  Verified: { bg: "#e7f0ff", fg: "#1e3a8a" },
  Approved: { bg: "#dcfce7", fg: "#15803d" },
  Published: { bg: "#d1fae5", fg: "#047857" },
  Rejected: { bg: "#fee2e2", fg: "#b91c1c" },
  // Extraction statuses
  Pending: { bg: "#eef2f7", fg: "#475569" },
  Validated: { bg: "#e0edff", fg: "#1d4ed8" },
  Processing: { bg: "#fff4e0", fg: "#b45309" },
  Completed: { bg: "#dcfce7", fg: "#15803d" },
  Reviewed: { bg: "#ede9fe", fg: "#6d28d9" },
  Failed: { bg: "#fee2e2", fg: "#b91c1c" },
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || { bg: "#eef2f7", fg: "#475569" };
  return (
    <span className="status-badge" style={{ background: style.bg, color: style.fg }}>
      <span className="dot" />
      {status || "—"}
    </span>
  );
}
