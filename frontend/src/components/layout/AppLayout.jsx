import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import Footer from "./Footer";
import Breadcrumb from "./Breadcrumb";

/** Authenticated app shell: fixed sidebar + sticky navbar + content + footer. */
export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Close the mobile sidebar whenever the route changes.
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="app-shell">
      <Sidebar open={sidebarOpen} onNavigate={closeSidebar} />
      <div className={`sidebar-backdrop ${sidebarOpen ? "show" : ""}`} onClick={closeSidebar} />

      <div className="app-main">
        <Navbar onToggleSidebar={() => setSidebarOpen((v) => !v)} />
        <main className="app-content">
          <div className="mb-3">
            <Breadcrumb />
          </div>
          <div key={location.pathname} className="fade-in">
            <Outlet />
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}
