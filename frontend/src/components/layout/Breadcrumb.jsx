import { Link, useLocation } from "react-router-dom";

const LABELS = {
  dashboard: "Dashboard",
  byelaws: "Bye-laws",
  upload: "Upload",
  search: "Search",
  approvals: "Approvals",
  users: "Users",
  roles: "Roles & Permissions",
  audit: "Audit Log",
  profile: "Profile",
  settings: "Settings",
};

function labelFor(segment) {
  if (LABELS[segment]) return LABELS[segment];
  if (/^\d+$/.test(segment)) return `#${segment}`;
  return segment.charAt(0).toUpperCase() + segment.slice(1);
}

export default function Breadcrumb() {
  const { pathname } = useLocation();
  const segments = pathname.split("/").filter(Boolean);

  return (
    <nav aria-label="breadcrumb">
      <ol className="breadcrumb">
        <li className="breadcrumb-item">
          <Link to="/dashboard">
            <i className="bi bi-house-door" />
          </Link>
        </li>
        {segments.map((seg, idx) => {
          const to = "/" + segments.slice(0, idx + 1).join("/");
          const isLast = idx === segments.length - 1;
          return (
            <li key={to} className={`breadcrumb-item ${isLast ? "active" : ""}`} aria-current={isLast ? "page" : undefined}>
              {isLast ? labelFor(seg) : <Link to={to}>{labelFor(seg)}</Link>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
