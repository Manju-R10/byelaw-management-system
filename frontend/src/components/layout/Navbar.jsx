import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { notificationApi } from "../../api/notifications";
import { initials, timeAgo } from "../../utils/format";

export default function Navbar({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notifs, setNotifs] = useState({ items: [], unread: 0 });
  const [openMenu, setOpenMenu] = useState(null); // "notif" | "user" | null
  const wrapRef = useRef(null);

  async function loadNotifs() {
    try {
      const { data } = await notificationApi.list({ page_size: 6 });
      setNotifs({ items: data.items, unread: data.unread_count });
    } catch {
      /* non-blocking */
    }
  }

  useEffect(() => {
    loadNotifs();
    const id = setInterval(loadNotifs, 60000); // light polling
    return () => clearInterval(id);
  }, []);

  // Close dropdowns on outside click.
  useEffect(() => {
    const onClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpenMenu(null);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  async function handleMarkAll() {
    try {
      await notificationApi.markAllRead();
      loadNotifs();
    } catch {
      /* ignore */
    }
  }

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="app-navbar">
      <button className="icon-btn d-lg-none" onClick={onToggleSidebar} aria-label="Toggle menu">
        <i className="bi bi-list" />
      </button>

      <div className="fw-semibold text-strong d-none d-sm-block">
        Cooperative Society Bye-law Management
      </div>

      <div className="ms-auto d-flex align-items-center gap-2" ref={wrapRef}>
        {/* Notifications */}
        <div className="position-relative">
          <button
            className="icon-btn"
            aria-label="Notifications"
            onClick={() => setOpenMenu(openMenu === "notif" ? null : "notif")}
          >
            <i className="bi bi-bell" />
            {notifs.unread > 0 && <span className="notif-dot">{notifs.unread > 9 ? "9+" : notifs.unread}</span>}
          </button>
          {openMenu === "notif" && (
            <div className="card shadow-lg p-0 fade-in" style={dropdownStyle}>
              <div className="d-flex align-items-center justify-content-between px-3 py-2 border-bottom">
                <span className="fw-semibold">Notifications</span>
                {notifs.unread > 0 && (
                  <button className="btn btn-sm btn-link p-0 text-decoration-none" onClick={handleMarkAll}>
                    Mark all read
                  </button>
                )}
              </div>
              <div style={{ maxHeight: 320, overflowY: "auto" }}>
                {notifs.items.length === 0 ? (
                  <div className="text-center text-muted small py-4">You're all caught up</div>
                ) : (
                  notifs.items.map((n) => (
                    <div key={n.notification_id} className={`px-3 py-2 border-bottom ${n.is_read ? "" : "bg-light"}`}>
                      <div className="small fw-semibold text-truncate">{n.title}</div>
                      <div className="small text-muted text-truncate">{n.message}</div>
                      <div className="text-muted" style={{ fontSize: "0.68rem" }}>{timeAgo(n.created_at)}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User menu */}
        <div className="position-relative">
          <button
            className="d-flex align-items-center gap-2 btn p-1"
            onClick={() => setOpenMenu(openMenu === "user" ? null : "user")}
          >
            <span className="avatar">{initials(user?.full_name || user?.username)}</span>
            <span className="d-none d-md-flex flex-column align-items-start lh-1">
              <span className="fw-semibold small">{user?.full_name}</span>
              <span className="text-muted" style={{ fontSize: "0.72rem" }}>{user?.role_name}</span>
            </span>
            <i className="bi bi-chevron-down small text-muted d-none d-md-block" />
          </button>
          {openMenu === "user" && (
            <div className="card shadow-lg p-0 fade-in" style={{ ...dropdownStyle, width: 220 }}>
              <div className="px-3 py-2 border-bottom">
                <div className="fw-semibold small">{user?.full_name}</div>
                <div className="text-muted" style={{ fontSize: "0.72rem" }}>{user?.email || user?.username}</div>
              </div>
              <Link to="/profile" className="dropdown-item-row" onClick={() => setOpenMenu(null)}>
                <i className="bi bi-person" /> Profile
              </Link>
              <Link to="/settings" className="dropdown-item-row" onClick={() => setOpenMenu(null)}>
                <i className="bi bi-gear" /> Settings
              </Link>
              <button className="dropdown-item-row text-danger border-0 bg-transparent w-100" onClick={handleLogout}>
                <i className="bi bi-box-arrow-right" /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

const dropdownStyle = {
  position: "absolute",
  right: 0,
  top: "calc(100% + 8px)",
  width: 320,
  zIndex: 1050,
  border: "1px solid var(--border-soft)",
};
