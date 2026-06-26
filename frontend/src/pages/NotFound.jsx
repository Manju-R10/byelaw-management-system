import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center text-center" style={{ minHeight: "60vh" }}>
      <div className="fw-bold text-brand" style={{ fontSize: "5rem", lineHeight: 1 }}>404</div>
      <h3 className="fw-bold mt-2">Page not found</h3>
      <p className="muted">The page you're looking for doesn't exist or has moved.</p>
      <Link to="/dashboard" className="btn btn-primary mt-2">
        <i className="bi bi-house-door me-2" /> Go to Dashboard
      </Link>
    </div>
  );
}
