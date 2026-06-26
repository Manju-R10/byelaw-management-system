/** Animated skeleton placeholder. */
export function Skeleton({ width = "100%", height = 14, className = "", style = {} }) {
  return <span className={`skeleton d-inline-block ${className}`} style={{ width, height, ...style }} />;
}

/** A few stacked skeleton lines, e.g. for table rows or list items. */
export function SkeletonLines({ rows = 3, className = "" }) {
  return (
    <div className={className}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="d-flex align-items-center gap-3 py-2">
          <Skeleton width={40} height={40} style={{ borderRadius: 10 }} />
          <div className="flex-grow-1">
            <Skeleton width="60%" height={12} className="mb-2" />
            <Skeleton width="35%" height={10} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonCard({ height = 90 }) {
  return <Skeleton height={height} style={{ borderRadius: 14, display: "block" }} />;
}
