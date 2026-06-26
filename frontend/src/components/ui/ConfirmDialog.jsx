import { useState } from "react";
import Modal from "./Modal";

/**
 * Confirmation dialog. Pass an async `onConfirm`; the dialog shows a spinner while it
 * runs and closes on success. `variant` controls the confirm button colour.
 */
export default function ConfirmDialog({
  open,
  title = "Are you sure?",
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "primary",
  icon = "bi-exclamation-triangle",
  onConfirm,
  onClose,
}) {
  const [busy, setBusy] = useState(false);

  async function handleConfirm() {
    setBusy(true);
    try {
      await onConfirm?.();
    } finally {
      setBusy(false);
    }
  }

  const danger = variant === "danger";

  return (
    <Modal
      open={open}
      size="sm"
      title={title}
      onClose={busy ? undefined : onClose}
      footer={
        <>
          <button className="btn btn-light" onClick={onClose} disabled={busy}>{cancelText}</button>
          <button className={`btn ${danger ? "btn-danger" : "btn-primary"}`} onClick={handleConfirm} disabled={busy}>
            {busy ? <span className="spinner-border spinner-border-sm me-2" /> : <i className={`bi ${danger ? "bi-trash" : "bi-check-lg"} me-2`} />}
            {confirmText}
          </button>
        </>
      }
    >
      <div className="d-flex gap-3">
        <div className="d-grid flex-shrink-0" style={{ width: 44, height: 44, placeItems: "center", borderRadius: 12, background: danger ? "#fee2e2" : "#eef2ff", color: danger ? "#b91c1c" : "#1e3a8a", fontSize: "1.3rem" }}>
          <i className={`bi ${icon}`} />
        </div>
        <div className="text-secondary" style={{ paddingTop: 2 }}>{message}</div>
      </div>
    </Modal>
  );
}
