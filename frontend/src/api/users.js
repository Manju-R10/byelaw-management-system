import api from "./client";

export const userApi = {
  list: (params = {}) => api.get("/users", { params }),
  get: (id) => api.get(`/users/${id}`),
  create: (payload) => api.post("/users", payload),
  update: (id, payload) => api.put(`/users/${id}`, payload),
  remove: (id) => api.delete(`/users/${id}`),
  resetPassword: (id, new_password) => api.post(`/users/${id}/reset-password`, { new_password }),
};
