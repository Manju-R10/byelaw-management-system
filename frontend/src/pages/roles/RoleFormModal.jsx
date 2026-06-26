import { useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";
import Modal from "../../components/ui/Modal";
import { roleApi } from "../../api/roles";
import { getApiError } from "../../api/client";

const SYSTEM_ROLES = ["Administrator", "Data Entry Operator", "Verifying Officer", "Viewer"];

const GROUP_LABELS = {
  USER: "User Management",
  ROLE: "Role Management",
  PERMISSION: "Permissions",
  BYELAW: "Bye-laws",
  AUDIT: "Audit",
};

function groupPermissions(permissions) {
  const groups = {};
  for (const p of permissions) {
    const key = p.permission_code.split("_")[0];
    (groups[key] = groups[key] || []).push(p);
  }
  return groups;
}

export default function RoleFormModal({ open, role, permissions, onClose, onSaved }) {
  const isEdit = !!role;
  const isSystem = isEdit && SYSTEM_ROLES.includes(role.role_name);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState(new Set());
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const grouped = useMemo(() => groupPermissions(permissions), [permissions]);

  useEffect(() => {
    if (open) {
      setErrors({});
      setName(role?.role_name || "");
      setDescription(role?.description || "");
      setSelected(new Set((role?.permissions || []).map((p) => p.permission_id)));
    }
  }, [open, role]);

  function toggle(id) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleGroup(items, on) {
    setSelected((prev) => {
      const next = new Set(prev);
      items.forEach((p) => (on ? next.add(p.permission_id) : next.delete(p.permission_id)));
      return next;
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!isEdit && (!name.trim() || name.trim().length < 2)) {
      setErrors({ name: "Role name must be at least 2 characters." });
      return;
    }
    setSaving(true);
    try {
      const permission_ids = [...selected];
      if (isEdit) {
        await roleApi.update(role.role_id, { description: description.trim() || null, permission_ids });
        toast.success("Role updated.");
      } else {
        await roleApi.create({ role_name: name.trim(), description: description.trim() || null, permission_ids });
        toast.success("Role created.");
      }
      onSaved?.();
      onClose?.();
    } catch (err) {
      toast.error(getApiError(err, "Could not save the role."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      open={open}
      size="lg"
      title={isEdit ? `Edit role — ${role.role_name}` : "Create role"}
      onClose={saving ? undefined : onClose}
      footer={
        <>
          <button className="btn btn-light" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" form="role-form" type="submit" disabled={saving}>
            {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check-lg me-2" />}
            {isEdit ? "Save changes" : "Create role"}
          </button>
        </>
      }
    >
      <form id="role-form" onSubmit={handleSubmit} noValidate>
        <div className="row g-3 mb-2">
          <div className="col-12 col-sm-5">
            <label className="form-label">Role name {!isEdit && <span className="req">*</span>}</label>
            <input className={`form-control ${errors.name ? "is-invalid" : ""}`} value={name} onChange={(e) => setName(e.target.value)} disabled={isEdit} placeholder="e.g. Auditor" />
            {isSystem && <div className="form-hint"><i className="bi bi-lock me-1" />System role — name is protected.</div>}
            {errors.name && <div className="field-error">{errors.name}</div>}
          </div>
          <div className="col-12 col-sm-7">
            <label className="form-label">Description</label>
            <input className="form-control" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What this role is for" />
          </div>
        </div>

        <label className="form-label mt-2">Permissions <span className="text-muted">({selected.size} selected)</span></label>
        <div style={{ maxHeight: 340, overflowY: "auto" }}>
          {Object.entries(grouped).map(([key, items]) => {
            const allOn = items.every((p) => selected.has(p.permission_id));
            return (
              <div className="perm-group" key={key}>
                <div className="d-flex align-items-center justify-content-between">
                  <span className="perm-group-title mb-0">{GROUP_LABELS[key] || key}</span>
                  <button type="button" className="btn btn-sm btn-link p-0 text-decoration-none" onClick={() => toggleGroup(items, !allOn)}>
                    {allOn ? "Clear" : "Select all"}
                  </button>
                </div>
                <div className="row">
                  {items.map((p) => (
                    <div className="col-12 col-md-6" key={p.permission_id}>
                      <div className="perm-item">
                        <input type="checkbox" className="form-check-input mt-1" id={`perm-${p.permission_id}`} checked={selected.has(p.permission_id)} onChange={() => toggle(p.permission_id)} />
                        <label htmlFor={`perm-${p.permission_id}`}>
                          <span className="code d-block">{p.permission_code}</span>
                          <span className="text-muted small">{p.description}</span>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </form>
    </Modal>
  );
}
