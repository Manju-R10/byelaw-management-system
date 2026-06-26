import api from "./client";

export const byelawApi = {
  list: (params = {}) => api.get("/byelaws", { params }),
  get: (id) => api.get(`/byelaws/${id}`),
  upload: (formData, onUploadProgress) =>
    api.post("/byelaws/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    }),
};
