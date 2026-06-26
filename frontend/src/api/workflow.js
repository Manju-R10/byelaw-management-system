import api from "./client";

export const workflowApi = {
  transition: (masterId, action, remarks) =>
    api.post(`/byelaws/${masterId}/workflow/${action}`, remarks ? { remarks } : {}),
  history: (masterId) => api.get(`/byelaws/${masterId}/workflow/history`),
  versions: (masterId) => api.get(`/byelaws/${masterId}/versions`),
};

/** Permission + source-state requirements per workflow action (mirrors the backend). */
export const WORKFLOW_ACTIONS = {
  submit: { label: "Submit for review", icon: "bi-send", permission: "BYELAW_EDIT", from: ["Draft", "Rejected"], variant: "primary" },
  "start-review": { label: "Start review", icon: "bi-clipboard-check", permission: "BYELAW_VERIFY", from: ["Submitted"], variant: "primary" },
  verify: { label: "Verify", icon: "bi-check2-circle", permission: "BYELAW_VERIFY", from: ["Under Review"], variant: "primary" },
  approve: { label: "Approve", icon: "bi-patch-check", permission: "BYELAW_VERIFY", from: ["Verified"], variant: "accent" },
  publish: { label: "Publish as active", icon: "bi-broadcast", permission: "BYELAW_PUBLISH", from: ["Approved"], variant: "accent" },
  reject: { label: "Reject", icon: "bi-x-octagon", permission: "BYELAW_VERIFY", from: ["Submitted", "Under Review", "Verified"], variant: "danger", requiresRemarks: true },
  "return-to-draft": { label: "Return to draft", icon: "bi-arrow-counterclockwise", permission: "BYELAW_EDIT", from: ["Rejected"], variant: "light" },
};
