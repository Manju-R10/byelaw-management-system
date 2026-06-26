import api from "./client";

export const roleApi = {
  list: () => api.get("/roles"),
  get: (id) => api.get(`/roles/${id}`),
  create: (payload) => api.post("/roles", payload),
  update: (id, payload) => api.put(`/roles/${id}`, payload),
  remove: (id) => api.delete(`/roles/${id}`),
  permissions: () => api.get("/permissions"),
};
