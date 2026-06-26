import { useState } from "react";
import { toast } from "react-toastify";
import Modal from "../ui/Modal";
import { useAuth } from "../../context/AuthContext";
import { workflowApi, WORKFLOW_ACTIONS } from "../../api/workflow";
import { getApiError } from "../../api/client";

const VARIANT_BTN = { primary: "btn-primary", accent: "btn-accent", danger: "btn-danger", light: "btn-light" };

/** Renders the workflow transitions permitted for the current status + user role. */
export default function WorkflowActions({ masterId, status, onDone, size = "" }) {
  const { hasPermission } = useAuth();
  const [active, setActive] = useState(null); // action key
  const [remarks, setRemarks] = useState("");
  const [busy, setBusy] = useState(false);

  const available = Object.entries(WORKFLOW_ACTIONS).filter(
    ([, a]) => a.from.includes(status) && hasPermission(a.permission)
  );

  function open(key) { setActive(key); setRemarks(""); }

  async function confirm() {
    const action = WORKFLOW_ACTIONS[active];
    if (action.requiresRemarks && !remarks.trim()) { toast.warn("Remarks are required for this action."); return; }
    setBusy(true);
    try {
      const { data } = await workflowApi.transition(masterId, active, remarks.trim() || undefined);
      toast.success(data.message || "Status updated.");
      setActive(null);
      onDone?.(data);
    } catch (err) {
      toast.error(getApiError(err, "Could not update the workflow status."));
    } finally {
      setBusy(false);
    }
  }

  if (available.length === 0) {
    return <span className="text-muted small"><i className="bi bi-info-circle me-1" />No workflow actions available for your role at this stage.</span>;
  }

  const dialogAction = active ? WORKFLOW_ACTIONS[active] : null;

  return (
    <>
      <div className="d-flex flex-wrap gap-2">
        {available.map(([key, a]) => (
          <button key={key} className={`btn ${size} ${VARIANT_BTN[a.variant] || "btn-primary"}`} onClick={() => open(key)}>
            <i className={`bi ${a.icon} me-2`} />{a.label}
          </button>
        ))}
      </div>

      <Modal
        open={!!active}
        size="sm"
        title={dialogAction?.label}
        onClose={busy ? undefined : () => setActive(null)}
        footer={
          <>
            <button className="btn btn-light" onClick={() => setActive(null)} disabled={busy}>Cancel</button>
            <button className={`btn ${VARIANT_BTN[dialogAction?.variant] || "btn-primary"}`} onClick={confirm} disabled={busy}>
              {busy ? <span className="spinner-border spinner-border-sm me-2" /> : <i className={`bi ${dialogAction?.icon} me-2`} />}Confirm
            </button>
          </>
        }
      >
        <p className="text-secondary mb-2">
          Confirm <strong>{dialogAction?.label}</strong> for this bye-law?
        </p>
        <label className="form-label">Remarks {dialogAction?.requiresRemarks ? <span className="req">*</span> : <span className="text-muted">(optional)</span>}</label>
        <textarea className="form-control" rows={3} value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Add a note for the audit trail…" autoFocus />
      </Modal>
    </>
  );
}
