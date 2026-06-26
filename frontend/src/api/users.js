import api from "./client";

export const userApi = {
  list: (params = {}) => api.get("/users", { params }),
  get: (id) => api.get(`/users/${id}`),
};
