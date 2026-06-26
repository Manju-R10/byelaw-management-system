import api from "./client";

export const notificationApi = {
  list: (params = {}) => api.get("/notifications", { params }),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post("/notifications/read-all"),
};
