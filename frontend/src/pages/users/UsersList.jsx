import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";
import { userApi } from "../../api/users";
import { roleApi } from "../../api/roles";
import { getApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { usePagedList } from "../../hooks/usePagedList";
import { useDebounce } from "../../hooks/useDebounce";
import PageHeader from "../../components/ui/PageHeader";
import Pagination from "../../components/ui/Pagination";
import StatusBadge from "../../components/ui/StatusBadge";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonLines } from "../../components/ui/Skeleton";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import UserFormModal from "./UserFormModal";
import ResetPasswordModal from "./ResetPasswordModal";
import { formatDate, initials } from "../../utils/format";

export default function UsersList() {
  const { user: me, hasPermission } = useAuth();
  const canCreate = hasPermission("USER_CREATE");
  const canUpdate = hasPermission("USER_UPDATE");
  const canDelete = hasPermission("USER_DELETE");

  const [roles, setRoles] = useState([]);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 350);

  const fetcher = useCallback((params) => userApi.list(params), []);
  const list = usePagedList(fetcher, { pageSize: 10 });

  const [formOpen, setFormOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [resetUser, setResetUser] = useState(null);
  const [deleteUser, setDeleteUser] = useState(null);

  useEffect(() => {
    roleApi.list().then((r) => setRoles(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    list.setFilter("search", debouncedSearch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const activeFilters = useMemo(
    () => Object.entries(list.filters).filter(([k, v]) => v !== "" && v != null && k !== "search"),
    [list.filters]
  );

  async function confirmDelete() {
    try {
      await userApi.remove(deleteUser.user_id);
      toast.success(`User '${deleteUser.username}' deleted.`);
      setDeleteUser(null);
      list.reload();
    } catch (err) {
      toast.error(getApiError(err, "Could not delete the user."));
    }
  }

  return (
    <div>
      <PageHeader
        title="User Management"
        subtitle="Create and manage system users and their roles."
        icon="bi-people"
        actions={canCreate && (
          <button className="btn btn-primary" onClick={() => { setEditUser(null); setFormOpen(true); }}>
            <i className="bi bi-plus-lg me-2" />New user
          </button>
        )}
      />

      <div className="app-card">
        {/* Toolbar */}
        <div className="toolbar">
          <div className="search-box">
            <i className="bi bi-search" />
            <input className="form-control" placeholder="Search by name, username or email…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="form-select" style={{ maxWidth: 180 }} value={list.filters.role_id || ""} onChange={(e) => list.setFilter("role_id", e.target.value || "")}>
            <option value="">All roles</option>
            {roles.map((r) => <option key={r.role_id} value={r.role_id}>{r.role_name}</option>)}
          </select>
          <select className="form-select" style={{ maxWidth: 150 }} value={list.filters.is_active ?? ""} onChange={(e) => list.setFilter("is_active", e.target.value)}>
            <option value="">All statuses</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        {/* Table */}
        <div className="table-responsive">
          {list.loading ? (
            <div className="p-3"><SkeletonLines rows={6} /></div>
          ) : list.error ? (
            <EmptyState icon="bi-exclamation-octagon" title="Couldn't load users" subtitle={list.error} />
          ) : list.items.length === 0 ? (
            <EmptyState icon="bi-people" title="No users found" subtitle={search || activeFilters.length ? "Try adjusting your search or filters." : "Create your first user to get started."} />
          ) : (
            <table className="table table-hover align-middle mb-0">
              <thead>
                <tr><th>User</th><th>Role</th><th>Status</th><th>Created</th><th className="text-end">Actions</th></tr>
              </thead>
              <tbody>
                {list.items.map((u) => (
                  <tr key={u.user_id}>
                    <td>
                      <div className="d-flex align-items-center gap-2">
                        <span className="avatar" style={{ width: 36, height: 36, fontSize: "0.8rem" }}>{initials(u.full_name)}</span>
                        <div className="min-w-0">
                          <div className="fw-semibold">{u.full_name} {u.user_id === me?.user_id && <span className="badge text-bg-light ms-1">You</span>}</div>
                          <div className="text-muted small">@{u.username}{u.email ? ` · ${u.email}` : ""}</div>
                        </div>
                      </div>
                    </td>
                    <td>{u.role_name || "—"}</td>
                    <td>
                      <span className="status-badge" style={u.is_active ? { background: "#dcfce7", color: "#15803d" } : { background: "#fee2e2", color: "#b91c1c" }}>
                        <span className="dot" />{u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="text-muted small">{formatDate(u.created_at)}</td>
                    <td className="text-end">
                      <div className="btn-group btn-group-sm">
                        {canUpdate && <button className="btn btn-outline-secondary" title="Edit" onClick={() => { setEditUser(u); setFormOpen(true); }}><i className="bi bi-pencil" /></button>}
                        {canUpdate && <button className="btn btn-outline-secondary" title="Reset password" onClick={() => setResetUser(u)}><i className="bi bi-key" /></button>}
                        {canDelete && <button className="btn btn-outline-danger" title="Delete" onClick={() => setDeleteUser(u)} disabled={u.user_id === me?.user_id}><i className="bi bi-trash" /></button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {!list.loading && <Pagination page={list.page} totalPages={list.totalPages} total={list.total} pageSize={list.pageSize} onChange={list.setPage} />}
      </div>

      <UserFormModal open={formOpen} user={editUser} roles={roles} onClose={() => setFormOpen(false)} onSaved={list.reload} />
      <ResetPasswordModal open={!!resetUser} user={resetUser} onClose={() => setResetUser(null)} />
      <ConfirmDialog
        open={!!deleteUser}
        title="Delete user"
        message={<>This will deactivate and remove <strong>{deleteUser?.full_name}</strong> (<code>{deleteUser?.username}</code>). This action cannot be undone.</>}
        confirmText="Delete user"
        variant="danger"
        onConfirm={confirmDelete}
        onClose={() => setDeleteUser(null)}
      />
    </div>
  );
}
