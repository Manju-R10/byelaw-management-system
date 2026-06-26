import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import { AuthProvider } from "./context/AuthContext";
import AppRoutes from "./routes/AppRoutes";
import ErrorBoundary from "./components/ErrorBoundary";
import { applyDensity } from "./utils/prefs";

export default function App() {
  // Apply the persisted UI density preference once at startup.
  useEffect(() => {
    applyDensity();
  }, []);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
          <ToastContainer position="top-right" autoClose={3500} newestOnTop theme="light" />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
