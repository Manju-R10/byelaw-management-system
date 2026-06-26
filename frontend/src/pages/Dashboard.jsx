import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { byelawApi } from "../api/byelaws";
import { userApi } from "../api/users";
import { notificationApi } from "../api/notifications";
import SummaryCard from "../components/ui/SummaryCard";
import StatusBadge from "../components/ui/StatusBadge";
import EmptyState from "../components/ui/EmptyState";
import { SkeletonLines } from "../components/ui/Skeleton";
import { formatDate, timeAgo } from "../utils/format";

export default function Dashboard() {
  const { user, hasPermission } = useAuth();
  const canSearch = hasPermission("BYELAW_SEARCH");
  const canReadUsers = hasPermission("USER_READ");

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, pending: 0, published: 0, users: 0 });
  const [recent, setRecent] = useState([]);
  const [pending, setPending] = useState([]);
  const [notifs, setNotifs] = useState({ items: [], unread: 0 });

  async function loadAll() {
    setLoading(true);
    try {
      const tasks = [];

      if (canSearch) {
        tasks.push(
          byelawApi.list({ page_size: 1 }),                                  // 0 total
          byelawApi.list({ page_size: 1, workflow_status: "Submitted" }),    // 1 pending
          byelawApi.list({ page_size: 1, workflow_status: "Published" }),    // 2 published
          byelawApi.list({ page: 1, page_size: 6 }),                         // 3 recent
          byelawApi.list({ page: 1, page_size: 5, workflow_status: "Submitted" }) // 4 pending list
        );
      }
      const notifReq = notificationApi.list({ page_size: 6 });
      const usersReq = canReadUsers ? userApi.list({ page_size: 1 }) : null;

      const results = await Promise.allSettled([...tasks, notifReq, ...(usersReq ? [usersReq] : [])]);

      let idx = 0;
      const next = { total: 0, pending: 0, published: 0, users: 0 };
      if (canSearch) {
        const get = (i) => (results[i]?.status === "fulfilled" ? results[i].value.data : null);
        next.total = get(0)?.total ?? 0;
        next.pending = get(1)?.total ?? 0;
        next.published = get(2)?.total ?? 0;
        setRecent(get(3)?.items ?? []);
        setPending(get(4)?.items ?? []);
        idx = 5;
      }
      const notifRes = results[idx];
      if (notifRes?.status === "fulfilled") {
        setNotifs({ items: notifRes.value.data.items, unread: notifRes.value.data.unread_count });
      }
      if (usersReq) {
        const uRes = results[idx + 1];
        if (uRes?.status === "fulfilled") next.users = uRes.value.data.total;
      }
      setStats(next);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function markAllRead() {
    try {
      await notificationApi.markAllRead();
      loadAll();
    } catch {
      /* ignore */
    }
  }

  const cards = [
    canSearch && { icon: "bi-journal-text", value: stats.total, label: "Total Bye-laws", color: "#1e3a8a", tint: "#eef2ff" },
    canSearch && { icon: "bi-hourglass-split", value: stats.pending, label: "Pending Approvals", color: "#b45309", tint: "#fff4e0" },
    canSearch && { icon: "bi-patch-check", value: stats.published, label: "Published & Active", color: "#047857", tint: "#dcfce7" },
    canReadUsers
      ? { icon: "bi-people", value: stats.users, label: "System Users", color: "#6d28d9", tint: "#ede9fe" }
      : { icon: "bi-bell", value: notifs.unread, label: "Unread Notifications", color: "#1e3a8a", tint: "#eef2ff" },
  ].filter(Boolean);

  return (
    <div>
      <div className="section-head">
        <div>
          <h1 className="page-title">Welcome back, {user?.full_name?.split(" ")[0] || user?.username} 👋</h1>
          <p className="muted mb-0">Here's an overview of your bye-law digitization workspace.</p>
        </div>
        {canSearch && (
          <Link to="/byelaws/upload" className="btn btn-primary">
            <i className="bi bi-cloud-arrow-up me-2" /> Upload Bye-law
          </Link>
        )}
      </div>

      {/* Summary cards */}
      <div className="row g-3 mb-4">
        {cards.map((c, i) => (
          <div className="col-12 col-sm-6 col-xl-3" key={i}>
            <SummaryCard {...c} loading={loading} />
          </div>
        ))}
      </div>

      <div className="row g-3">
        {/* Left column */}
        <div className="col-12 col-xl-8">
          {/* Recent uploads */}
          <div className="app-card mb-3">
            <div className="card-head">
              <h6><i className="bi bi-clock-history me-2 text-brand" />Recent Bye-laws</h6>
              {canSearch && <Link to="/byelaws" className="btn btn-sm btn-outline-primary">View all</Link>}
            </div>
            <div className="table-responsive">
              {loading ? (
                <div className="p-3"><SkeletonLines rows={4} /></div>
              ) : !canSearch ? (
                <EmptyState icon="bi-lock" title="No access" subtitle="Your role cannot view bye-laws." />
              ) : recent.length === 0 ? (
                <EmptyState icon="bi-journal" title="No bye-laws yet" subtitle="Uploaded bye-laws will appear here." />
              ) : (
                <table className="table table-hover mb-0 align-middle">
                  <thead>
                    <tr>
                      <th>Society</th><th>Title</th><th>Version</th><th>Extraction</th><th>Workflow</th><th>Uploaded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((b) => (
                      <tr key={b.master_id}>
                        <td className="fw-semibold">{b.society_name}<div className="text-muted small">{b.society_registration_no}</div></td>
                        <td>{b.byelaw_title}</td>
                        <td>{b.byelaw_version}</td>
                        <td><StatusBadge status={b.extraction_status} /></td>
                        <td><StatusBadge status={b.workflow_status} /></td>
                        <td className="text-muted small">{formatDate(b.uploaded_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Pending approvals */}
          <div className="app-card">
            <div className="card-head">
              <h6><i className="bi bi-hourglass-split me-2 text-brand" />Pending Approvals</h6>
              <span className="badge text-bg-light">{pending.length}</span>
            </div>
            <div className="table-responsive">
              {loading ? (
                <div className="p-3"><SkeletonLines rows={3} /></div>
              ) : pending.length === 0 ? (
                <EmptyState icon="bi-check2-circle" title="No items awaiting approval" subtitle="Submitted bye-laws will show up here." />
              ) : (
                <table className="table table-hover mb-0 align-middle">
                  <thead>
                    <tr><th>Society</th><th>Title</th><th>Version</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {pending.map((b) => (
                      <tr key={b.master_id}>
                        <td className="fw-semibold">{b.society_name}</td>
                        <td>{b.byelaw_title}</td>
                        <td>{b.byelaw_version}</td>
                        <td><StatusBadge status={b.workflow_status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="col-12 col-xl-4">
          {/* Notifications */}
          <div className="app-card mb-3">
            <div className="card-head">
              <h6><i className="bi bi-bell me-2 text-brand" />Notifications {notifs.unread > 0 && <span className="badge bg-accent ms-1">{notifs.unread}</span>}</h6>
              {notifs.unread > 0 && <button className="btn btn-sm btn-link text-decoration-none p-0" onClick={markAllRead}>Mark all read</button>}
            </div>
            <div className="p-2">
              {loading ? (
                <SkeletonLines rows={3} />
              ) : notifs.items.length === 0 ? (
                <EmptyState icon="bi-bell-slash" title="No notifications" />
              ) : (
                notifs.items.map((n) => (
                  <div key={n.notification_id} className={`d-flex gap-2 p-2 rounded ${n.is_read ? "" : "bg-light"}`}>
                    <i className="bi bi-dot fs-4 lh-1" style={{ color: n.is_read ? "#cbd5e1" : "#10b981" }} />
                    <div className="min-w-0">
                      <div className="small fw-semibold text-truncate">{n.title}</div>
                      <div className="small text-muted">{n.message}</div>
                      <div className="text-muted" style={{ fontSize: "0.68rem" }}>{timeAgo(n.created_at)}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent activity */}
          <div className="app-card">
            <div className="card-head"><h6><i className="bi bi-activity me-2 text-brand" />Recent Activity</h6></div>
            <div className="p-3">
              {loading ? (
                <SkeletonLines rows={3} />
              ) : recent.length === 0 ? (
                <EmptyState icon="bi-activity" title="No recent activity" />
              ) : (
                <div className="timeline">
                  {recent.slice(0, 5).map((b) => (
                    <div className="timeline-item" key={b.master_id}>
                      <div className="small fw-semibold">{b.byelaw_title} <span className="text-muted">v{b.byelaw_version}</span></div>
                      <div className="small text-muted">{b.society_name} · uploaded</div>
                      <div className="text-muted" style={{ fontSize: "0.68rem" }}>{timeAgo(b.uploaded_date)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
