import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import Modal from "../ui/Modal";
import { clauseApi } from "../../api/clauses";
import { getApiError } from "../../api/client";

const LEVELS = [
  { value: 1, label: "1 — Chapter" },
  { value: 2, label: "2 — Clause" },
  { value: 3, label: "3 — Sub-clause" },
  { value: 4, label: "4 — Nested" },
];

/** Add or edit a clause. mode: "add" (optionally under `parent`) | "edit" (of `clause`). */
export default function ClauseFormModal({ open, mode, clause, parent, masterId, onClose, onSaved }) {
  const isEdit = mode === "edit";
  const [form, setForm] = useState({ clause_no: "", chapter_no: "", clause_title: "", clause_text: "", clause_level: 2 });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError("");
    if (isEdit && clause) {
      setForm({
        clause_no: clause.clause_no || "",
        chapter_no: clause.chapter_no || "",
        clause_title: clause.clause_title || "",
        clause_text: clause.clause_text || "",
        clause_level: clause.clause_level || 2,
      });
    } else {
      const lvl = parent ? Math.min((parent.clause_level || 1) + 1, 6) : 1;
      setForm({ clause_no: "", chapter_no: "", clause_title: "", clause_text: "", clause_level: lvl });
    }
  }, [open, isEdit, clause, parent]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.clause_text.trim()) { setError("Clause text is required."); return; }
    setSaving(true);
    try {
      if (isEdit) {
        await clauseApi.update(clause.clause_id, {
          clause_title: form.clause_title.trim() || null,
          clause_text: form.clause_text,
          clause_no: form.clause_no.trim() || null,
          chapter_no: form.chapter_no.trim() || null,
          clause_level: Number(form.clause_level),
        });
        toast.success("Clause updated.");
      } else {
        await clauseApi.add(masterId, {
          parent_clause_id: parent?.clause_id ?? null,
          clause_level: Number(form.clause_level),
          clause_no: form.clause_no.trim() || null,
          chapter_no: form.chapter_no.trim() || null,
          clause_title: form.clause_title.trim() || null,
          clause_text: form.clause_text,
        });
        toast.success("Clause added.");
      }
      onSaved?.();
      onClose?.();
    } catch (err) {
      toast.error(getApiError(err, "Could not save the clause."));
    } finally {
      setSaving(false);
    }
  }

  const title = isEdit ? "Edit clause" : parent ? `Add sub-clause under ${parent.clause_no || parent.clause_title || "clause"}` : "Add clause";

  return (
    <Modal
      open={open}
      size="lg"
      title={title}
      onClose={saving ? undefined : onClose}
      footer={
        <>
          <button className="btn btn-light" onClick={onClose} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" form="clause-form" type="submit" disabled={saving}>
            {saving ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-check-lg me-2" />}
            {isEdit ? "Save" : "Add clause"}
          </button>
        </>
      }
    >
      <form id="clause-form" onSubmit={handleSubmit} noValidate>
        <div className="row g-3">
          <div className="col-6 col-md-3">
            <label className="form-label">Number</label>
            <input className="form-control" value={form.clause_no} onChange={(e) => set("clause_no", e.target.value)} placeholder="e.g. 5.1.2" />
          </div>
          <div className="col-6 col-md-3">
            <label className="form-label">Chapter no.</label>
            <input className="form-control" value={form.chapter_no} onChange={(e) => set("chapter_no", e.target.value)} placeholder="optional" />
          </div>
          <div className="col-12 col-md-6">
            <label className="form-label">Level</label>
            <select className="form-select" value={form.clause_level} onChange={(e) => set("clause_level", e.target.value)}>
              {LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
        </div>
        <div className="mt-3">
          <label className="form-label">Title / Heading</label>
          <input className="form-control" value={form.clause_title} onChange={(e) => set("clause_title", e.target.value)} placeholder="Heading text (optional)" />
        </div>
        <div className="mt-3">
          <label className="form-label">Clause text <span className="req">*</span></label>
          <textarea className={`form-control ${error ? "is-invalid" : ""}`} rows={6} value={form.clause_text} onChange={(e) => { set("clause_text", e.target.value); setError(""); }} placeholder="Full body text of the clause" />
          {error && <div className="field-error">{error}</div>}
        </div>
      </form>
    </Modal>
  );
}
