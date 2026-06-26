import { useCallback, useEffect, useState } from "react";
import { toast } from "react-toastify";
import { notificationApi } from "../../api/notifications";
import { getApiError } from "../../api/client";
import PageHeader from "../../components/ui/PageHeader";
import Pagination from "../../components/ui/Pagination";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonLines } from "../../components/ui/Skeleton";
import { formatDate, timeAgo } from "../../utils/format";

export default function Notifications() {
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const pageSize = 15;
  const [data, setData] = useState({ items: [], total: 0, total_pages: 0, unread_count: 0 });
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await notificationApi.list({ page, page_size: pageSize, unread_only: unreadOnly });
      setData(data);
    } catch (err) {
      toast.error(getApiError(err, "Couldn't load notifications."));
    } finally {
      setLoading(false);
    }
  }, [page, unreadOnly]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setPage(1); }, [unreadOnly]);

  async function markRead(id) {
    try { await notificationApi.markRead(id); load(); } catch { /* ignore */ }
  }
  async function markAll() {
    try { await notificationApi.markAllRead(); toast.success("All notifications marked as read."); load(); }
    catch (err) { toast.error(getApiError(err)); }
  }

  return (
    <div>
      <PageHeader
        title="Notifications"
        subtitle="Workflow updates and system messages addressed to you."
        icon="bi-bell"
        actions={data.unread_count > 0 && <button className="btn btn-outline-primary" onClick={markAll}><i className="bi bi-check2-all me-2" />Mark all read</button>}
      />

      <div className="app-card">
        <div className="toolbar">
          <div className="form-check form-switch">
            <input className="form-check-input" type="checkbox" id="unread-only" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
            <label className="form-check-label" htmlFor="unread-only">Unread only</label>
          </div>
          {data.unread_count > 0 && <span className="filter-chip">{data.unread_count} unread</span>}
        </div>

        {loading ? (
          <div className="p-3"><SkeletonLines rows={6} /></div>
        ) : data.items.length === 0 ? (
          <EmptyState icon="bi-bell-slash" title={unreadOnly ? "No unread notifications" : "No notifications yet"} subtitle="You're all caught up." />
        ) : (
          <div>
            {data.items.map((n) => (
              <div key={n.notification_id} className={`d-flex gap-3 px-3 py-3 border-bottom ${n.is_read ? "" : "bg-light"}`}>
                <div className="d-grid flex-shrink-0" style={{ width: 40, height: 40, placeItems: "center", borderRadius: 11, background: n.is_read ? "#eef2f7" : "#eef2ff", color: n.is_read ? "#94a3b8" : "#1e3a8a" }}>
                  <i className="bi bi-bell" />
                </div>
                <div className="flex-grow-1 min-w-0">
                  <div className="fw-semibold">{n.title}</div>
                  <div className="text-secondary small">{n.message}</div>
                  <div className="text-muted" style={{ fontSize: "0.72rem" }}>{formatDate(n.created_at, true)} · {timeAgo(n.created_at)}</div>
                </div>
                {!n.is_read && (
                  <button className="btn btn-sm btn-light align-self-center" onClick={() => markRead(n.notification_id)} title="Mark as read">
                    <i className="bi bi-check-lg" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {!loading && <Pagination page={page} totalPages={data.total_pages} total={data.total} pageSize={pageSize} onChange={setPage} />}
      </div>
    </div>
  );
}
