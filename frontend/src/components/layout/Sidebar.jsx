import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { getVisibleSections } from "../../config/navigation";

export default function Sidebar({ open, onNavigate }) {
  const { hasPermission } = useAuth();
  const sections = getVisibleSections(hasPermission);

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="sidebar-brand">
        <div className="logo">
          <i className="bi bi-journal-bookmark-fill" />
        </div>
        <div>
          <div className="title">Bye-law System</div>
          <div className="subtitle">C-DIT · Co-operative Dept.</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`}
              >
                <i className={`bi ${item.icon}`} />
                <span>{item.label}</span>
                {!item.ready && <span className="soon-badge">SOON</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div>Version 1.0.0</div>
        <div>© {new Date().getFullYear()} C-DIT, Govt. of Kerala</div>
      </div>
    </aside>
  );
}
