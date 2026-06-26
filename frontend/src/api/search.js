import api from "./client";

export const searchApi = {
  clauses: (params = {}) => api.get("/search/clauses", { params }),
  byelaws: (params = {}) => api.get("/search/byelaws", { params }),
};
