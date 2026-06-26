import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import Modal from "../../components/ui/Modal";
import { userApi } from "../../api/users";
import { getApiError } from "../../api/client";

export default function ResetPasswordModal({ open, user, onClose }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) { setPassword(""); setError(""); }
  }, [open]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setError("Password must be at least 8 characters and include a letter and a digit.");
      return;
    }
    setSaving(true);
    try {
      await userApi.resetPassword(user.user_id, password);
      toast.success(`Password reset for ${user.username}. They must sign in again.`);
      onClose?.();
    } catch (err) {
      toast.error(getApiError(err, "Could not reset the password."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      size="sm"
      title="Reset password"
      onClose={saving ? undefined : onClose}
      footer={
        <>
          <button className="btn btn-light" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" form="reset-pwd-form" type="submit" disabled={saving}>
            {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-key me-2" />}Reset
          </button>
        </>
      }
    >
      <form id="reset-pwd-form" onSubmit={handleSubmit} noValidate>
        <p className="muted small">Set a new password for <strong>{user?.full_name}</strong> (<code>{user?.username}</code>).</p>
        <label className="form-label">New password</label>
        <input type="text" className={`form-control ${error ? "is-invalid" : ""}`} value={password} onChange={(e) => { setPassword(e.target.value); setError(""); }} placeholder="Min 8 chars, a letter and a digit" autoFocus />
        {error && <div className="field-error">{error}</div>}
      </form>
    </Modal>
  );
}
