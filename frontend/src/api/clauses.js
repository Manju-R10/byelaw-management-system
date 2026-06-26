import api from "./client";

// Extraction parses the whole document and can legitimately take a minute or more for
// large bye-laws (e.g. the 100+ page ULCCS document ~70s). The global 30s axios timeout
// would abort the request mid-extraction and surface a false "Extract failed" even though
// the backend completes successfully — so these heavy operations get generous timeouts.
const EXTRACT_TIMEOUT_MS = 600000; // 10 minutes
const REORDER_TIMEOUT_MS = 120000; // 2 minutes (bulk update of many clauses)

export const clauseApi = {
  extract: (masterId) => api.post(`/byelaws/${masterId}/extract`, null, { timeout: EXTRACT_TIMEOUT_MS }),
  tree: (masterId) => api.get(`/byelaws/${masterId}/clauses`),
  add: (masterId, payload) => api.post(`/byelaws/${masterId}/clauses`, payload),
  reorder: (masterId, items) => api.post(`/byelaws/${masterId}/clauses/reorder`, { items }, { timeout: REORDER_TIMEOUT_MS }),
  markReviewed: (masterId) => api.post(`/byelaws/${masterId}/mark-reviewed`),
  update: (clauseId, payload) => api.put(`/clauses/${clauseId}`, payload),
  remove: (clauseId) => api.delete(`/clauses/${clauseId}`),
};
