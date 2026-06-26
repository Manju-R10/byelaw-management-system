import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "react-toastify";
import { byelawApi } from "../../api/byelaws";
import { clauseApi } from "../../api/clauses";
import { workflowApi } from "../../api/workflow";
import { getApiError } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import StatusBadge from "../../components/ui/StatusBadge";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonLines } from "../../components/ui/Skeleton";
import ConfirmDialog from "../../components/ui/ConfirmDialog";
import ClauseTree from "../../components/clauses/ClauseTree";
import ClauseFormModal from "../../components/clauses/ClauseFormModal";
import WorkflowActions from "../../components/workflow/WorkflowActions";
import { formatDate, timeAgo } from "../../utils/format";
import { flattenForReorder, indent, moveDown, moveUp, outdent } from "../../utils/clauseTree";

const WF_STAGES = ["Draft", "Submitted", "Under Review", "Verified", "Approved", "Published"];
const EDITABLE_STATES = ["Draft", "Rejected"];

export default function ByelawDetail() {
  const { id } = useParams();
  const masterId = Number(id);
  const navigate = useNavigate();
  const { hasPermission } = useAuth();

  const [byelaw, setByelaw] = useState(null);
  const [tree, setTree] = useState([]);
  const [history, setHistory] = useState([]);
  const [versions, setVersions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("details");

  const [extracting, setExtracting] = useState(false);
  const [warnings, setWarnings] = useState([]);

  const [clauseModal, setClauseModal] = useState({ open: false, mode: "add", clause: null, parent: null });
  const [deleteClause, setDeleteClause] = useState(null);

  const canExtract = hasPermission("BYELAW_EXTRACT");
  const canEdit = hasPermission("BYELAW_EDIT");

  const loadCore = useCallback(async () => {
    const [b, t] = await Promise.all([byelawApi.get(masterId), clauseApi.tree(masterId)]);
    setByelaw(b.data);
    setTree(t.data);
  }, [masterId]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [, , h, v] = await Promise.allSettled([
        byelawApi.get(masterId).then((r) => setByelaw(r.data)),
        clauseApi.tree(masterId).then((r) => setTree(r.data)),
        workflowApi.history(masterId).then((r) => setHistory(r.data)).catch(() => {}),
        workflowApi.versions(masterId).then((r) => setVersions(r.data)).catch(() => {}),
      ]);
      void h; void v;
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }, [masterId]);

  useEffect(() => { loadAll(); }, [loadAll]);

  async function refreshAfterWorkflow() {
    await Promise.allSettled([
      byelawApi.get(masterId).then((r) => setByelaw(r.data)),
      workflowApi.history(masterId).then((r) => setHistory(r.data)),
      workflowApi.versions(masterId).then((r) => setVersions(r.data)),
    ]);
  }

  async function runExtraction() {
    setExtracting(true);
    setWarnings([]);
    const pending = toast.loading("Extracting clauses… large documents may take up to a minute.");
    try {
      const { data } = await clauseApi.extract(masterId);
      // Reload the Head record (counts/status) and the clause hierarchy, then surface warnings.
      await loadCore();
      setWarnings(data.warnings || []);
      setTab("clauses");
      toast.update(pending, {
        render: data.message || "Extraction complete.",
        type: "success",
        isLoading: false,
        autoClose: 4000,
      });
    } catch (err) {
      toast.update(pending, {
        render: getApiError(err, "Extraction failed."),
        type: "error",
        isLoading: false,
        autoClose: 5000,
      });
    } finally {
      setExtracting(false);
    }
  }

  async function markReviewed() {
    try {
      const { data } = await clauseApi.markReviewed(masterId);
      setByelaw(data);
      toast.success("Bye-law marked as reviewed.");
    } catch (err) {
      toast.error(getApiError(err, "Could not mark as reviewed."));
    }
  }

  // --- clause review handlers ---
  const editable = canEdit && EDITABLE_STATES.includes(byelaw?.workflow_status);

  async function handleMove(clauseId, dir) {
    const ops = { up: moveUp, down: moveDown, indent, outdent };
    const newTree = ops[dir](tree, clauseId);
    setTree(newTree); // optimistic
    try {
      await clauseApi.reorder(masterId, flattenForReorder(newTree));
      const t = await clauseApi.tree(masterId);
      setTree(t.data);
    } catch (err) {
      toast.error(getApiError(err, "Could not reorder clauses."));
      const t = await clauseApi.tree(masterId);
      setTree(t.data);
    }
  }

  async function confirmDeleteClause() {
    try {
      await clauseApi.remove(deleteClause.clause_id);
      toast.success("Clause deleted.");
      setDeleteClause(null);
      await loadCore();
    } catch (err) {
      toast.error(getApiError(err, "Could not delete the clause."));
    }
  }

  const reviewHandlers = {
    onEdit: (node) => setClauseModal({ open: true, mode: "edit", clause: node, parent: null }),
    onAddChild: (node) => setClauseModal({ open: true, mode: "add", clause: null, parent: node }),
    onDelete: (node) => setDeleteClause(node),
    onMove: handleMove,
  };

  if (loading) {
    return <div className="app-card p-3"><SkeletonLines rows={6} /></div>;
  }
  if (error || !byelaw) {
    return <div className="app-card"><EmptyState icon="bi-exclamation-octagon" title="Couldn't load bye-law" subtitle={error || "Not found."} /></div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="d-flex align-items-center gap-2 mb-2">
        <button className="btn btn-sm btn-light" onClick={() => navigate("/byelaws")}><i className="bi bi-arrow-left me-1" />Back</button>
      </div>

      <div className="app-card p-3 mb-3">
        <div className="d-flex flex-wrap justify-content-between gap-3">
          <div className="min-w-0">
            <div className="d-flex align-items-center gap-2 flex-wrap">
              <h1 className="page-title mb-0">{byelaw.byelaw_title}</h1>
              {byelaw.is_active && <span className="status-badge" style={{ background: "#d1fae5", color: "#047857" }}><span className="dot" />Active version</span>}
            </div>
            <div className="muted">{byelaw.society_name} · {byelaw.society_registration_no} · v{byelaw.byelaw_version}</div>
            <div className="d-flex gap-2 mt-2 flex-wrap">
              <StatusBadge status={byelaw.extraction_status} />
              <StatusBadge status={byelaw.workflow_status} />
              <span className="text-muted small"><i className="bi bi-diagram-3 me-1" />{byelaw.total_chapters} chapters · {byelaw.total_clauses} clauses</span>
            </div>
          </div>
          <div className="d-flex flex-column gap-2 align-items-end">
            {canExtract && byelaw.workflow_status === "Draft" && (
              <button className="btn btn-primary" onClick={runExtraction} disabled={extracting}>
                {extracting ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-cpu me-2" />}
                {byelaw.total_clauses > 0 ? "Re-extract clauses" : "Extract clauses"}
              </button>
            )}
            {canEdit && byelaw.total_clauses > 0 && byelaw.extraction_status === "Completed" && (
              <button className="btn btn-outline-primary" onClick={markReviewed}><i className="bi bi-check2-all me-2" />Mark as reviewed</button>
            )}
          </div>
        </div>
      </div>

      {warnings.length > 0 && (
        <div className="alert alert-warning d-flex gap-2">
          <i className="bi bi-exclamation-triangle-fill mt-1" />
          <div>
            <strong>{warnings.length} numbering anomaly(ies) flagged for review:</strong>
            <ul className="mb-0 mt-1 small">{warnings.slice(0, 6).map((w, i) => <li key={i}>{w}</li>)}</ul>
            {warnings.length > 6 && <div className="small">…and {warnings.length - 6} more.</div>}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="app-tabs mb-3">
        {[
          ["details", "Details", "bi-info-circle"],
          ["clauses", `Clauses (${byelaw.total_clauses})`, "bi-diagram-3"],
          ["workflow", "Workflow", "bi-check2-square"],
          ["versions", "Versions", "bi-layers"],
        ].map(([key, label, icon]) => (
          <button key={key} className={`app-tab ${tab === key ? "active" : ""}`} onClick={() => setTab(key)}>
            <i className={`bi ${icon} me-2`} />{label}
          </button>
        ))}
      </div>

      {tab === "details" && <DetailsTab byelaw={byelaw} />}
      {tab === "clauses" && (
        <ClausesTab
          byelaw={byelaw} tree={tree} editable={editable} canExtract={canExtract}
          onExtract={runExtraction} extracting={extracting}
          onAddTop={() => setClauseModal({ open: true, mode: "add", clause: null, parent: null })}
          handlers={reviewHandlers}
        />
      )}
      {tab === "workflow" && <WorkflowTab byelaw={byelaw} history={history} onDone={refreshAfterWorkflow} />}
      {tab === "versions" && <VersionsTab versions={versions} currentId={masterId} />}

      <ClauseFormModal
        open={clauseModal.open}
        mode={clauseModal.mode}
        clause={clauseModal.clause}
        parent={clauseModal.parent}
        masterId={masterId}
        onClose={() => setClauseModal((m) => ({ ...m, open: false }))}
        onSaved={loadCore}
      />
      <ConfirmDialog
        open={!!deleteClause}
        title="Delete clause"
        message={<>Delete this clause and all of its sub-clauses? This cannot be undone.</>}
        confirmText="Delete"
        variant="danger"
        onConfirm={confirmDeleteClause}
        onClose={() => setDeleteClause(null)}
      />
    </div>
  );
}

function DetailsTab({ byelaw }) {
  const rows = [
    ["Society name", byelaw.society_name],
    ["Registration no.", byelaw.society_registration_no],
    ["Society type", byelaw.society_type || "—"],
    ["Bye-law title", byelaw.byelaw_title],
    ["Version", byelaw.byelaw_version],
    ["Effective date", formatDate(byelaw.effective_date)],
    ["Registrar approval no.", byelaw.registrar_approval_no || "—"],
    ["Approval date", formatDate(byelaw.approval_date)],
    ["Source file", byelaw.source_file_name],
    ["File type", byelaw.source_file_type],
    ["Chapters / Clauses", `${byelaw.total_chapters} / ${byelaw.total_clauses}`],
    ["Uploaded", formatDate(byelaw.uploaded_date, true)],
    ["Reviewed", byelaw.reviewed_date ? formatDate(byelaw.reviewed_date, true) : "—"],
  ];
  return (
    <div className="app-card p-4">
      <div className="detail-meta">
        {rows.map(([label, value]) => (
          <div key={label}>
            <div className="dm-label">{label}</div>
            <div className="dm-value">{value}</div>
          </div>
        ))}
      </div>
      {byelaw.remarks && (
        <div className="mt-4">
          <div className="dm-label">Remarks</div>
          <div className="dm-value" style={{ whiteSpace: "pre-wrap" }}>{byelaw.remarks}</div>
        </div>
      )}
    </div>
  );
}

function ClausesTab({ byelaw, tree, editable, canExtract, onExtract, extracting, onAddTop, handlers }) {
  if (!tree || tree.length === 0) {
    return (
      <div className="app-card">
        <EmptyState
          icon="bi-diagram-3"
          title="No clauses extracted yet"
          subtitle={canExtract && byelaw.workflow_status === "Draft" ? "Run extraction to parse this document into a clause hierarchy." : "Clauses will appear here once extracted."}
        />
        {canExtract && byelaw.workflow_status === "Draft" && (
          <div className="text-center pb-4">
            <button className="btn btn-primary" onClick={onExtract} disabled={extracting}>
              {extracting ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-cpu me-2" />}Extract clauses
            </button>
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="app-card p-3">
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
        <div className="muted small">
          {editable ? <><i className="bi bi-pencil-square me-1" />Review mode — edit, re-order and re-parent clauses.</> : <><i className="bi bi-eye me-1" />Read-only view.</>}
        </div>
        {editable && <button className="btn btn-sm btn-outline-primary" onClick={onAddTop}><i className="bi bi-plus-lg me-1" />Add top-level clause</button>}
      </div>
      <ClauseTree nodes={tree} editable={editable} handlers={handlers} />
    </div>
  );
}

function WorkflowTab({ byelaw, history, onDone }) {
  const status = byelaw.workflow_status;
  const rejected = status === "Rejected";
  const currentIdx = WF_STAGES.indexOf(status);

  return (
    <div className="row g-3">
      <div className="col-12 col-lg-7">
        <div className="app-card p-3 mb-3">
          <h6 className="fw-bold mb-3">Current status</h6>
          <div className="wf-steps mb-2">
            {WF_STAGES.map((stage, i) => {
              const done = currentIdx >= 0 && i < currentIdx;
              const current = stage === status;
              return (
                <span key={stage} className={`wf-step ${done ? "done" : ""} ${current ? "current" : ""}`}>
                  <span className="num">{done ? <i className="bi bi-check" /> : i + 1}</span>{stage}
                  {i < WF_STAGES.length - 1 && <i className="bi bi-chevron-right chev" />}
                </span>
              );
            })}
          </div>
          {rejected && <div className="alert alert-danger py-2 mb-0 mt-2"><i className="bi bi-x-octagon me-2" />This bye-law was rejected and returned to the uploader.</div>}
        </div>

        <div className="app-card p-3">
          <h6 className="fw-bold mb-3">Available actions</h6>
          <WorkflowActions masterId={byelaw.master_id} status={status} onDone={onDone} />
        </div>
      </div>

      <div className="col-12 col-lg-5">
        <div className="app-card p-3">
          <h6 className="fw-bold mb-3"><i className="bi bi-clock-history me-2 text-brand" />Workflow history</h6>
          {history.length === 0 ? (
            <EmptyState icon="bi-clock-history" title="No transitions yet" />
          ) : (
            <div className="timeline">
              {history.map((h) => (
                <div className="timeline-item" key={h.history_id}>
                  <div className="small fw-semibold">{h.previous_status ? `${h.previous_status} → ` : ""}{h.new_status}</div>
                  {h.remarks && <div className="small text-secondary">{h.remarks}</div>}
                  <div className="text-muted" style={{ fontSize: "0.68rem" }}>{formatDate(h.changed_at, true)} · {timeAgo(h.changed_at)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function VersionsTab({ versions, currentId }) {
  if (!versions) return <div className="app-card"><EmptyState icon="bi-layers" title="No version data" /></div>;
  return (
    <div className="app-card">
      <div className="card-head"><h6><i className="bi bi-layers me-2 text-brand" />Versions for {versions.society_registration_no}</h6><span className="badge text-bg-light">{versions.total_versions} total</span></div>
      <div className="table-responsive">
        <table className="table table-hover align-middle mb-0">
          <thead><tr><th>Version</th><th>Status</th><th>Active</th><th>Effective</th><th>Uploaded</th><th></th></tr></thead>
          <tbody>
            {versions.versions.map((v) => (
              <tr key={v.master_id} className={v.master_id === currentId ? "table-active" : ""}>
                <td className="fw-semibold">v{v.byelaw_version}{v.master_id === currentId && <span className="badge text-bg-light ms-2">Viewing</span>}</td>
                <td><StatusBadge status={v.workflow_status} /></td>
                <td>{v.is_active ? <span className="text-accent"><i className="bi bi-check-circle-fill me-1" />Active</span> : <span className="text-muted">—</span>}</td>
                <td className="text-muted small">{formatDate(v.effective_date)}</td>
                <td className="text-muted small">{formatDate(v.uploaded_date)}</td>
                <td className="text-end">{v.master_id !== currentId && <Link className="btn btn-sm btn-outline-secondary" to={`/byelaws/${v.master_id}`}>Open</Link>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
