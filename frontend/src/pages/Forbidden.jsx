import { Link } from "react-router-dom";

export default function Forbidden() {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center text-center" style={{ minHeight: "60vh" }}>
      <div className="mb-3 d-grid" style={{ width: 80, height: 80, placeItems: "center", borderRadius: 20, background: "#fee2e2", color: "#b91c1c", fontSize: "2.2rem" }}>
        <i className="bi bi-shield-lock" />
      </div>
      <h3 className="fw-bold">Access denied</h3>
      <p className="muted">You don't have permission to view this page.</p>
      <Link to="/dashboard" className="btn btn-primary mt-2">
        <i className="bi bi-house-door me-2" /> Back to Dashboard
      </Link>
    </div>
  );
}
