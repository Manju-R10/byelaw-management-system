import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../api/auth";
import { tokenStore } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => tokenStore.getUser());
  const [bootstrapping, setBootstrapping] = useState(true);

  // On first load, if a token exists, validate it and refresh the profile.
  useEffect(() => {
    let active = true;
    async function bootstrap() {
      if (!tokenStore.getAccess()) {
        setBootstrapping(false);
        return;
      }
      try {
        const { data } = await authApi.me();
        if (active) {
          setUser(data);
          tokenStore.setUser(data);
        }
      } catch {
        if (active) {
          tokenStore.clear();
          setUser(null);
        }
      } finally {
        if (active) setBootstrapping(false);
      }
    }
    bootstrap();
    return () => {
      active = false;
    };
  }, []);

  // React to forced session expiry dispatched by the axios interceptor.
  useEffect(() => {
    const onExpired = () => {
      tokenStore.clear();
      setUser(null);
    };
    window.addEventListener("auth:expired", onExpired);
    return () => window.removeEventListener("auth:expired", onExpired);
  }, []);

  const login = useCallback(async (username, password) => {
    const { data } = await authApi.login(username, password);
    tokenStore.setTokens(data);
    tokenStore.setUser(data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefresh();
    try {
      if (refresh) await authApi.logout(refresh);
    } catch {
      /* best-effort */
    } finally {
      tokenStore.clear();
      setUser(null);
    }
  }, []);

  const hasPermission = useCallback(
    (code) => !!user?.permissions?.includes(code),
    [user]
  );
  const hasAnyPermission = useCallback(
    (codes = []) => codes.some((c) => user?.permissions?.includes(c)),
    [user]
  );

  const value = useMemo(
    () => ({
      user,
      setUser,
      bootstrapping,
      isAuthenticated: !!user,
      login,
      logout,
      hasPermission,
      hasAnyPermission,
    }),
    [user, bootstrapping, login, logout, hasPermission, hasAnyPermission]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
