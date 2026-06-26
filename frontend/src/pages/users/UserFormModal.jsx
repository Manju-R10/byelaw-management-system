import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import Modal from "../../components/ui/Modal";
import { userApi } from "../../api/users";
import { getApiError } from "../../api/client";

const EMPTY = { username: "", full_name: "", email: "", role_id: "", is_active: true, password: "" };

export default function UserFormModal({ open, user, roles, onClose, onSaved }) {
  const isEdit = !!user;
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setErrors({});
      setForm(
        user
          ? { username: user.username, full_name: user.full_name, email: user.email || "", role_id: user.role_id, is_active: user.is_active, password: "" }
          : { ...EMPTY, role_id: roles[0]?.role_id || "" }
      );
    }
  }, [open, user, roles]);

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: undefined }));
  }

  function validate() {
    const e = {};
    if (!isEdit) {
      if (!form.username.trim() || form.username.trim().length < 3) e.username = "Username must be at least 3 characters.";
      else if (!/^[A-Za-z0-9_.-]+$/.test(form.username.trim())) e.username = "Only letters, digits, '.', '_' and '-' are allowed.";
      if (!form.password || form.password.length < 8) e.password = "Password must be at least 8 characters.";
      else if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) e.password = "Include at least one letter and one digit.";
    }
    if (!form.full_name.trim()) e.full_name = "Full name is required.";
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Enter a valid email address.";
    if (!form.role_id) e.role_id = "Please select a role.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      if (isEdit) {
        await userApi.update(user.user_id, {
          full_name: form.full_name.trim(),
          email: form.email.trim() || null,
          role_id: Number(form.role_id),
          is_active: form.is_active,
        });
        toast.success("User updated.");
      } else {
        await userApi.create({
          username: form.username.trim(),
          password: form.password,
          full_name: form.full_name.trim(),
          email: form.email.trim() || null,
          role_id: Number(form.role_id),
          is_active: form.is_active,
        });
        toast.success("User created.");
      }
      onSaved?.();
      onClose?.();
    } catch (err) {
      toast.error(getApiError(err, "Could not save the user."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      title={isEdit ? "Edit user" : "Create user"}
      onClose={saving ? undefined : onClose}
      footer={
        <>
          <button className="btn btn-light" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" form="user-form" type="submit" disabled={saving}>
            {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check-lg me-2" />}
            {isEdit ? "Save changes" : "Create user"}
          </button>
        </>
      }
    >
      <form id="user-form" onSubmit={handleSubmit} noValidate>
        <div className="mb-3">
          <label className="form-label">Username {!isEdit && <span className="req">*</span>}</label>
          <input
            className={`form-control ${errors.username ? "is-invalid" : ""}`}
            value={form.username}
            onChange={(e) => set("username", e.target.value)}
            disabled={isEdit}
            placeholder="e.g. data_operator_1"
          />
          {isEdit && <div className="form-hint">Username cannot be changed.</div>}
          {errors.username && <div className="field-error">{errors.username}</div>}
        </div>

        <div className="mb-3">
          <label className="form-label">Full name <span className="req">*</span></label>
          <input className={`form-control ${errors.full_name ? "is-invalid" : ""}`} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
          {errors.full_name && <div className="field-error">{errors.full_name}</div>}
        </div>

        <div className="row g-3">
          <div className="col-12 col-sm-6">
            <label className="form-label">Email</label>
            <input className={`form-control ${errors.email ? "is-invalid" : ""}`} value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="name@cdit.gov.in" />
            {errors.email && <div className="field-error">{errors.email}</div>}
          </div>
          <div className="col-12 col-sm-6">
            <label className="form-label">Role <span className="req">*</span></label>
            <select className={`form-select ${errors.role_id ? "is-invalid" : ""}`} value={form.role_id} onChange={(e) => set("role_id", e.target.value)}>
              <option value="">Select a role…</option>
              {roles.map((r) => <option key={r.role_id} value={r.role_id}>{r.role_name}</option>)}
            </select>
            {errors.role_id && <div className="field-error">{errors.role_id}</div>}
          </div>
        </div>

        {!isEdit && (
          <div className="mt-3">
            <label className="form-label">Temporary password <span className="req">*</span></label>
            <input type="text" className={`form-control ${errors.password ? "is-invalid" : ""}`} value={form.password} onChange={(e) => set("password", e.target.value)} placeholder="Min 8 chars, with a letter and a digit" />
            {errors.password ? <div className="field-error">{errors.password}</div> : <div className="form-hint">The user can change this after first sign-in.</div>}
          </div>
        )}

        <div className="form-check form-switch mt-3">
          <input className="form-check-input" type="checkbox" id="active-switch" checked={form.is_active} onChange={(e) => set("is_active", e.target.checked)} />
          <label className="form-check-label" htmlFor="active-switch">Active account</label>
        </div>
      </form>
    </Modal>
  );
}
