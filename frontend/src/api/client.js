import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const ACCESS_KEY = "blms_access";
const REFRESH_KEY = "blms_refresh";
const USER_KEY = "blms_user";

/** Small wrapper around localStorage for auth tokens and the cached user profile. */
export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  getUser: () => {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  setTokens: ({ access_token, refresh_token }) => {
    if (access_token) localStorage.setItem(ACCESS_KEY, access_token);
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
  },
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Attach the bearer token to every request.
api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Single in-flight refresh shared across concurrent 401s.
let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = tokenStore.getRefresh();
  if (!refresh) throw new Error("No refresh token");
  const resp = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
  tokenStore.setTokens(resp.data);
  return resp.data.access_token;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;
    const isAuthRoute = original?.url?.includes("/auth/");

    if (status === 401 && original && !original._retry && !isAuthRoute && tokenStore.getRefresh()) {
      original._retry = true;
      try {
        refreshPromise = refreshPromise || refreshAccessToken();
        const newToken = await refreshPromise;
        refreshPromise = null;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (refreshErr) {
        refreshPromise = null;
        tokenStore.clear();
        // Notify the app to drop the session; AuthContext listens for this.
        window.dispatchEvent(new CustomEvent("auth:expired"));
        return Promise.reject(refreshErr);
      }
    }
    return Promise.reject(error);
  }
);

/** Extract a human-readable message from the backend's error envelope. */
export function getApiError(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  if (data?.error?.message) return data.error.message;
  if (typeof data?.detail === "string") return data.detail;
  // A client-side timeout/abort has no response — surface it clearly instead of a
  // generic failure (the server may still be processing a long-running request).
  if (error?.code === "ECONNABORTED" || /timeout/i.test(error?.message || "")) {
    return "The request took too long and timed out. The operation may still be processing on the server — please refresh in a moment.";
  }
  if (error?.message === "Network Error") return "Cannot reach the server. Is the backend running?";
  return fallback;
}

export default api;
