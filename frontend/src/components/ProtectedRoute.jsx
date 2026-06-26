import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Guards routes behind authentication and (optionally) a required permission.
 * Renders a full-screen loader while the auth state is still bootstrapping.
 */
export default function ProtectedRoute({ children, permission }) {
  const { isAuthenticated, bootstrapping, hasPermission } = useAuth();
  const location = useLocation();

  if (bootstrapping) {
    return (
      <div className="d-flex flex-column align-items-center justify-content-center vh-100 text-muted">
        <div className="spinner-border text-brand mb-3" role="status" aria-hidden="true" />
        <span>Loading your workspace…</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (permission && !hasPermission(permission)) {
    return <Navigate to="/forbidden" replace />;
  }

  return children;
}
