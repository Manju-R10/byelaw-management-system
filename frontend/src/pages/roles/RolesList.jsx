import { useCallback, useEffect, useState } from "react";
import { toast } from "react-toastify";
import { roleApi } from "../../api/roles";
import { getApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PageHeader from "../../components/ui/PageHeader";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonCard } from "../../components/ui/Skeleton";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import RoleFormModal from "./RoleFormModal";

const SYSTEM_ROLES = ["Administrator", "Data Entry Operator", "Verifying Officer", "Viewer"];
const ROLE_ICONS = {
  Administrator: "bi-shield-fill-check",
  "Data Entry Operator": "bi-pencil-square",
  "Verifying Officer": "bi-patch-check",
  Viewer: "bi-eye",
};

export default function RolesList() {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission("ROLE_CREATE");
  const canUpdate = hasPermission("ROLE_UPDATE");
  const canDelete = hasPermission("ROLE_DELETE");

  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editRole, setEditRole] = useState(null);
  const [deleteRole, setDeleteRole] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, p] = await Promise.all([roleApi.list(), roleApi.permissions().catch(() => ({ data: [] }))]);
      setRoles(r.data);
      setPermissions(p.data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function confirmDelete() {
    try {
      await roleApi.remove(deleteRole.role_id);
      toast.success(`Role '${deleteRole.role_name}' deleted.`);
      setDeleteRole(null);
      load();
    } catch (err) {
      toast.error(getApiError(err, "Could not delete the role."));
    }
  }

  return (
    <div>
      <PageHeader
        title="Roles & Permissions"
        subtitle="Define roles and assign granular permissions."
        icon="bi-shield-lock"
        actions={canCreate && (
          <button className="btn btn-primary" onClick={() => { setEditRole(null); setFormOpen(true); }}>
            <i className="bi bi-plus-lg me-2" />New role
          </button>
        )}
      />

      {loading ? (
        <div className="row g-3">
          {Array.from({ length: 4 }).map((_, i) => <div className="col-12 col-md-6 col-xl-4" key={i}><SkeletonCard height={150} /></div>)}
        </div>
      ) : error ? (
        <div className="app-card"><EmptyState icon="bi-exclamation-octagon" title="Couldn't load roles" subtitle={error} /></div>
      ) : (
        <div className="row g-3">
          {roles.map((role) => {
            const isSystem = SYSTEM_ROLES.includes(role.role_name);
            return (
              <div className="col-12 col-md-6 col-xl-4" key={role.role_id}>
                <div className="app-card h-100 hoverable p-3 d-flex flex-column">
                  <div className="d-flex align-items-start gap-2">
                    <div className="d-grid flex-shrink-0" style={{ width: 44, height: 44, placeItems: "center", borderRadius: 12, background: "#eef2ff", color: "#1e3a8a", fontSize: "1.2rem" }}>
                      <i className={`bi ${ROLE_ICONS[role.role_name] || "bi-people"}`} />
                    </div>
                    <div className="min-w-0 flex-grow-1">
                      <div className="fw-bold d-flex align-items-center gap-2">
                        {role.role_name}
                        {isSystem && <i className="bi bi-lock-fill text-muted small" title="System role" />}
                      </div>
                      <div className="text-muted small">{role.description || "No description"}</div>
                    </div>
                  </div>

                  <div className="d-flex gap-3 mt-3 small">
                    <span className="text-muted"><i className="bi bi-people me-1" />{role.user_count} user{role.user_count !== 1 ? "s" : ""}</span>
                    <span className="text-muted"><i className="bi bi-key me-1" />{role.permissions.length} permission{role.permissions.length !== 1 ? "s" : ""}</span>
                  </div>

                  <div className="d-flex flex-wrap gap-1 mt-2" style={{ maxHeight: 64, overflow: "hidden" }}>
                    {role.permissions.slice(0, 6).map((p) => <span key={p.permission_id} className="filter-chip">{p.permission_code}</span>)}
                    {role.permissions.length > 6 && <span className="filter-chip">+{role.permissions.length - 6}</span>}
                  </div>

                  <div className="mt-auto pt-3 d-flex gap-2">
                    {canUpdate && <button className="btn btn-sm btn-outline-primary flex-grow-1" onClick={() => { setEditRole(role); setFormOpen(true); }}><i className="bi bi-pencil me-1" />Edit</button>}
                    {canDelete && (
                      <button className="btn btn-sm btn-outline-danger" disabled={isSystem || role.user_count > 0} title={isSystem ? "System roles cannot be deleted" : role.user_count > 0 ? "Role has assigned users" : "Delete role"} onClick={() => setDeleteRole(role)}>
                        <i className="bi bi-trash" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <RoleFormModal open={formOpen} role={editRole} permissions={permissions} onClose={() => setFormOpen(false)} onSaved={load} />
      <ConfirmDialog
        open={!!deleteRole}
        title="Delete role"
        message={<>Delete the role <strong>{deleteRole?.role_name}</strong>? This cannot be undone.</>}
        confirmText="Delete role"
        variant="danger"
        onConfirm={confirmDelete}
        onClose={() => setDeleteRole(null)}
      />
    </div>
  );
}
