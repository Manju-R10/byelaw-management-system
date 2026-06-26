import api from "./client";

export const authApi = {
  login: (username, password) => api.post("/auth/login", { username, password }),
  refresh: (refresh_token) => api.post("/auth/refresh", { refresh_token }),
  logout: (refresh_token) => api.post("/auth/logout", { refresh_token }),
  me: () => api.get("/auth/me"),
  changePassword: (current_password, new_password) =>
    api.post("/users/me/change-password", { current_password, new_password }),
};
