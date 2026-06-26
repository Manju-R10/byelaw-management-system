import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import AppLayout from "../components/layout/AppLayout";
import Login from "../pages/Login";
import Dashboard from "../pages/Dashboard";
import UsersList from "../pages/users/UsersList";
import RolesList from "../pages/roles/RolesList";
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

        {/* Later phases (guarded placeholders) */}
        <Route path="/byelaws" element={<ProtectedRoute permission="BYELAW_SEARCH"><ComingSoon /></ProtectedRoute>} />
        <Route path="/byelaws/upload" element={<ProtectedRoute permission="BYELAW_UPLOAD"><ComingSoon /></ProtectedRoute>} />
        <Route path="/search" element={<ProtectedRoute permission="BYELAW_SEARCH"><ComingSoon /></ProtectedRoute>} />
        <Route path="/approvals" element={<ProtectedRoute permission="BYELAW_VERIFY"><ComingSoon /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute permission="USER_READ"><UsersList /></ProtectedRoute>} />
        <Route path="/roles" element={<ProtectedRoute permission="ROLE_READ"><RolesList /></ProtectedRoute>} />
        <Route path="/audit" element={<ProtectedRoute permission="AUDIT_VIEW"><ComingSoon /></ProtectedRoute>} />
        <Route path="/profile" element={<ComingSoon />} />
        <Route path="/settings" element={<ComingSoon />} />

        <Route path="/forbidden" element={<Forbidden />} />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
