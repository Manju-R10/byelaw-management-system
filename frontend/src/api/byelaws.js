import api from "./client";

export const byelawApi = {
  list: (params = {}) => api.get("/byelaws", { params }),
  get: (id) => api.get(`/byelaws/${id}`),
};
