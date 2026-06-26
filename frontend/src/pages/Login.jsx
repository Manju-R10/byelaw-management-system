import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";
import { getApiError } from "../api/client";

const DEMO_ACCOUNTS = [
  { role: "Administrator", username: "admin", password: "AdminPassword123" },
  { role: "Data Entry Operator", username: "operator", password: "OperatorPassword123" },
  { role: "Verifying Officer", username: "verifier", password: "VerifierPassword123" },
  { role: "Viewer", username: "viewer", password: "ViewerPassword123" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || "/dashboard";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password) {
      toast.warn("Please enter your username and password.");
      return;
    }
    setSubmitting(true);
    try {
      const user = await login(username.trim(), password);
      toast.success(`Welcome back, ${user.full_name}.`);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      toast.error(getApiError(err, "Login failed. Check your credentials."));
    } finally {
      setSubmitting(false);
    }
  }

  function fillDemo(acc) {
    setUsername(acc.username);
    setPassword(acc.password);
    setShowDemo(false);
  }

  return (
    <div className="login-wrap">
      {/* Hero / brand side */}
      <div className="login-hero">
        <div className="d-flex align-items-center gap-3">
          <div className="logo" style={{ width: 48, height: 48, borderRadius: 13, background: "rgba(255,255,255,0.12)", display: "grid", placeItems: "center", fontSize: "1.4rem" }}>
            <i className="bi bi-journal-bookmark-fill" />
          </div>
          <div>
            <div className="fw-bold">C-DIT</div>
            <div style={{ opacity: 0.8, fontSize: "0.82rem" }}>Centre for Development of Imaging Technology</div>
          </div>
        </div>

        <div>
          <h1 className="text-white fw-bold" style={{ fontSize: "2.1rem", lineHeight: 1.15 }}>
            Cooperative Society<br />Bye-law Management System
          </h1>
          <p style={{ opacity: 0.85, maxWidth: 460, marginTop: "1rem" }}>
            Digitize, extract, review and govern Cooperative Society bye-laws with a secure,
            auditable, clause-level workflow.
          </p>
          <div className="d-flex flex-wrap gap-3 mt-4">
            {[
              ["bi-shield-lock", "Role-based access"],
              ["bi-diagram-3", "Clause hierarchy"],
              ["bi-search", "Full-text search"],
              ["bi-check2-circle", "Approval workflow"],
            ].map(([icon, label]) => (
              <div key={label} className="d-flex align-items-center gap-2" style={{ opacity: 0.9, fontSize: "0.85rem" }}>
                <i className={`bi ${icon}`} /> {label}
              </div>
            ))}
          </div>
        </div>

        <div style={{ opacity: 0.7, fontSize: "0.78rem" }}>
          © {new Date().getFullYear()} C-DIT, Government of Kerala · Internal / Government Use
        </div>
      </div>

      {/* Form side */}
      <div className="login-form-side">
        <div className="login-card">
          <div className="text-center mb-4">
            <div className="d-lg-none mb-3">
              <span className="logo d-inline-grid" style={{ width: 52, height: 52, borderRadius: 14, background: "linear-gradient(135deg, var(--brand-primary-light), var(--brand-accent))", placeItems: "center", color: "#fff", fontSize: "1.4rem" }}>
                <i className="bi bi-journal-bookmark-fill" />
              </span>
            </div>
            <h2 className="fw-bold mb-1">Sign in</h2>
            <p className="muted mb-0">Access your bye-law management workspace</p>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-3">
              <label className="form-label fw-semibold small">Username</label>
              <div className="input-group">
                <span className="input-group-text bg-white"><i className="bi bi-person" /></span>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  autoFocus
                />
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold small">Password</label>
              <div className="input-group">
                <span className="input-group-text bg-white"><i className="bi bi-lock" /></span>
                <input
                  type={showPwd ? "text" : "password"}
                  className="form-control"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button type="button" className="btn btn-outline-secondary" onClick={() => setShowPwd((v) => !v)} tabIndex={-1} aria-label="Toggle password">
                  <i className={`bi ${showPwd ? "bi-eye-slash" : "bi-eye"}`} />
                </button>
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-100 py-2 fw-semibold" disabled={submitting}>
              {submitting ? (
                <><span className="spinner-border spinner-border-sm me-2" /> Signing in…</>
              ) : (
                <><i className="bi bi-box-arrow-in-right me-2" /> Sign in</>
              )}
            </button>
          </form>

          <div className="text-center mt-3">
            <button className="btn btn-sm btn-link text-decoration-none muted" onClick={() => setShowDemo((v) => !v)}>
              <i className="bi bi-info-circle me-1" /> Demo accounts
            </button>
          </div>
          {showDemo && (
            <div className="app-card p-2 mt-2 fade-in">
              {DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.username}
                  type="button"
                  className="dropdown-item-row w-100 border-0 bg-transparent rounded"
                  onClick={() => fillDemo(a)}
                >
                  <i className="bi bi-person-badge" />
                  <span className="flex-grow-1">
                    <span className="fw-semibold small">{a.role}</span>
                    <span className="text-muted small d-block">{a.username}</span>
                  </span>
                  <i className="bi bi-box-arrow-in-right text-muted" />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
