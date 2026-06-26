import api from "./client";

export const clauseApi = {
  extract: (masterId) => api.post(`/byelaws/${masterId}/extract`),
  tree: (masterId) => api.get(`/byelaws/${masterId}/clauses`),
  add: (masterId, payload) => api.post(`/byelaws/${masterId}/clauses`, payload),
  reorder: (masterId, items) => api.post(`/byelaws/${masterId}/clauses/reorder`, { items }),
  markReviewed: (masterId) => api.post(`/byelaws/${masterId}/mark-reviewed`),
  update: (clauseId, payload) => api.put(`/clauses/${clauseId}`, payload),
  remove: (clauseId) => api.delete(`/clauses/${clauseId}`),
};
