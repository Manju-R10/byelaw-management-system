import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";
import { authApi } from "../api/auth";
import { getApiError } from "../api/client";
import PageHeader from "../components/ui/PageHeader";
import { initials } from "../utils/format";

export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setErrors((e) => ({ ...e, [k]: undefined })); };

  function validate() {
    const e = {};
    if (!form.current_password) e.current_password = "Enter your current password.";
    if (form.new_password.length < 8 || !/[A-Za-z]/.test(form.new_password) || !/\d/.test(form.new_password))
      e.new_password = "Min 8 characters with at least one letter and one digit.";
    if (form.new_password !== form.confirm) e.confirm = "Passwords do not match.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      await authApi.changePassword(form.current_password, form.new_password);
      toast.success("Password changed. Please sign in again.");
      await logout();
      navigate("/login", { replace: true });
    } catch (err) {
      toast.error(getApiError(err, "Could not change the password."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <PageHeader title="My Profile" subtitle="Your account details and security settings." icon="bi-person" />

      <div className="row g-3">
        <div className="col-12 col-lg-5">
          <div className="app-card p-4 text-center h-100">
            <span className="avatar mx-auto" style={{ width: 84, height: 84, fontSize: "1.8rem", borderRadius: 22 }}>{initials(user?.full_name || user?.username)}</span>
            <h4 className="fw-bold mt-3 mb-0">{user?.full_name}</h4>
            <div className="muted">@{user?.username}</div>
            <span className="badge text-bg-light mt-2"><i className="bi bi-shield-lock me-1" />{user?.role_name}</span>

            <hr />
            <div className="text-start">
              <div className="dm-label">Email</div>
              <div className="dm-value mb-3">{user?.email || "—"}</div>
              <div className="dm-label">Permissions ({user?.permissions?.length || 0})</div>
              <div className="d-flex flex-wrap gap-1 mt-1">
                {user?.permissions?.map((p) => <span key={p} className="filter-chip">{p}</span>)}
              </div>
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-7">
          <div className="app-card p-4">
            <h6 className="fw-bold mb-3"><i className="bi bi-key me-2 text-brand" />Change password</h6>
            <form onSubmit={handleSubmit} noValidate style={{ maxWidth: 460 }}>
              <div className="mb-3">
                <label className="form-label">Current password</label>
                <input type="password" autoComplete="current-password" className={`form-control ${errors.current_password ? "is-invalid" : ""}`} value={form.current_password} onChange={(e) => set("current_password", e.target.value)} />
                {errors.current_password && <div className="field-error">{errors.current_password}</div>}
              </div>
              <div className="mb-3">
                <label className="form-label">New password</label>
                <input type="password" autoComplete="new-password" className={`form-control ${errors.new_password ? "is-invalid" : ""}`} value={form.new_password} onChange={(e) => set("new_password", e.target.value)} />
                {errors.new_password ? <div className="field-error">{errors.new_password}</div> : <div className="form-hint">Use at least 8 characters with a letter and a digit.</div>}
              </div>
              <div className="mb-3">
                <label className="form-label">Confirm new password</label>
                <input type="password" autoComplete="new-password" className={`form-control ${errors.confirm ? "is-invalid" : ""}`} value={form.confirm} onChange={(e) => set("confirm", e.target.value)} />
                {errors.confirm && <div className="field-error">{errors.confirm}</div>}
              </div>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check-lg me-2" />}Update password
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
