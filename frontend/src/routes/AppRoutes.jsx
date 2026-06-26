import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import AppLayout from "../components/layout/AppLayout";
import Login from "../pages/Login";
import Dashboard from "../pages/Dashboard";
import UsersList from "../pages/users/UsersList";
import RolesList from "../pages/roles/RolesList";
import ByelawsList from "../pages/byelaws/ByelawsList";
import UploadByelaw from "../pages/byelaws/UploadByelaw";
import ByelawDetail from "../pages/byelaws/ByelawDetail";
import Search from "../pages/search/Search";
import Approvals from "../pages/approvals/Approvals";
import Notifications from "../pages/notifications/Notifications";
import Profile from "../pages/Profile";
import Settings from "../pages/Settings";
import ComingSoon from "../pages/ComingSoon";
import Forbidden from "../pages/Forbidden";
import NotFound from "../pages/NotFound";

/**
 * Route table. Pages marked "Coming soon" are delivered in later frontend phases but
 * are routed (and permission-guarded) now so navigation is complete end-to-end.
 */
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />

        <Route path="/byelaws" element={<ProtectedRoute permission="BYELAW_SEARCH"><ByelawsList /></ProtectedRoute>} />
        <Route path="/byelaws/upload" element={<ProtectedRoute permission="BYELAW_UPLOAD"><UploadByelaw /></ProtectedRoute>} />
        <Route path="/byelaws/:id" element={<ProtectedRoute permission="BYELAW_SEARCH"><ByelawDetail /></ProtectedRoute>} />

        <Route path="/search" element={<ProtectedRoute permission="BYELAW_SEARCH"><Search /></ProtectedRoute>} />
        <Route path="/approvals" element={<ProtectedRoute permission="BYELAW_VERIFY"><Approvals /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute permission="USER_READ"><UsersList /></ProtectedRoute>} />
        <Route path="/roles" element={<ProtectedRoute permission="ROLE_READ"><RolesList /></ProtectedRoute>} />
        <Route path="/notifications" element={<Notifications />} />

        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />

        {/* Audit UI ships with the backend audit module (later milestone) */}
        <Route path="/audit" element={<ProtectedRoute permission="AUDIT_VIEW"><ComingSoon /></ProtectedRoute>} />

        <Route path="/forbidden" element={<Forbidden />} />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
