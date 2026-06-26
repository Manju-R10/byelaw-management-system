import { useLocation, Link } from "react-router-dom";

/** Placeholder for screens delivered in later frontend phases. */
export default function ComingSoon() {
  const { pathname } = useLocation();
  const name = pathname.split("/").filter(Boolean).map((s) => s[0].toUpperCase() + s.slice(1)).join(" / ");
  return (
    <div className="app-card p-5 text-center fade-in">
      <div className="mx-auto mb-3 d-grid" style={{ width: 72, height: 72, placeItems: "center", borderRadius: 18, background: "#eef2ff", color: "#1e3a8a", fontSize: "2rem" }}>
        <i className="bi bi-cone-striped" />
      </div>
      <h2 className="fw-bold mb-1">Coming soon</h2>
      <p className="muted">The <strong>{name || "this"}</strong> screen is part of an upcoming frontend phase.</p>
      <Link to="/dashboard" className="btn btn-primary mt-2">
        <i className="bi bi-arrow-left me-2" /> Back to Dashboard
      </Link>
    </div>
  );
}
