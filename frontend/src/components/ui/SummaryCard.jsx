import { SkeletonCard } from "./Skeleton";

/** Dashboard KPI card with an icon, value and label. */
export default function SummaryCard({ icon, value, label, color = "#1e3a8a", tint = "#eef2ff", loading }) {
  if (loading) return <SkeletonCard height={92} />;
  return (
    <div className="app-card summary-card hoverable fade-in h-100">
      <div className="sc-icon" style={{ background: tint, color }}>
        <i className={`bi ${icon}`} />
      </div>
      <div>
        <div className="sc-value">{value}</div>
        <div className="sc-label">{label}</div>
      </div>
    </div>
  );
}
