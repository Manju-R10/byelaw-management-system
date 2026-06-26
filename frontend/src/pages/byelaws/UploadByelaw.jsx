import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { byelawApi } from "../../api/byelaws";
import { getApiError } from "../../api/client";
import PageHeader from "../../components/ui/PageHeader";

const ACCEPTED = [".pdf", ".doc", ".docx"];
const MAX_MB = 25;

function extOf(name = "") {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i).toLowerCase() : "";
}

export default function UploadByelaw() {
  const navigate = useNavigate();
  const fileInput = useRef(null);

  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState({});
  const [meta, setMeta] = useState({
    society_name: "", society_registration_no: "", society_type: "",
    byelaw_title: "", byelaw_version: "", effective_date: "",
    registrar_approval_no: "", approval_date: "", remarks: "",
  });

  const set = (k, v) => { setMeta((m) => ({ ...m, [k]: v })); setErrors((e) => ({ ...e, [k]: undefined })); };

  function pickFile(f) {
    if (!f) return;
    if (!ACCEPTED.includes(extOf(f.name))) { toast.error(`Unsupported file type. Allowed: ${ACCEPTED.join(", ")}`); return; }
    if (f.size > MAX_MB * 1024 * 1024) { toast.error(`File exceeds the ${MAX_MB} MB limit.`); return; }
    if (f.size === 0) { toast.error("The selected file is empty."); return; }
    setFile(f);
    setErrors((e) => ({ ...e, file: undefined }));
  }

  function onDrop(e) {
    e.preventDefault(); setDrag(false);
    pickFile(e.dataTransfer.files?.[0]);
  }

  function validate() {
    const e = {};
    if (!file) e.file = "Please choose a bye-law document to upload.";
    if (!meta.society_name.trim()) e.society_name = "Society name is required.";
    if (!meta.society_registration_no.trim()) e.society_registration_no = "Registration number is required.";
    if (!meta.byelaw_title.trim()) e.byelaw_title = "Bye-law title is required.";
    if (!meta.byelaw_version.trim()) e.byelaw_version = "Version / amendment number is required.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    if (!validate()) { toast.warn("Please complete the required fields."); return; }
    const fd = new FormData();
    fd.append("file", file);
    Object.entries(meta).forEach(([k, v]) => { if (v) fd.append(k, v); });

    setUploading(true);
    setProgress(0);
    try {
      const { data } = await byelawApi.upload(fd, (e) => {
        if (e.total) setProgress(Math.round((e.loaded / e.total) * 100));
      });
      if (data.validation_passed) {
        toast.success(data.message || "Bye-law uploaded and validated.");
      } else {
        toast.warn(data.message || "Uploaded, but document validation failed.");
      }
      navigate(`/byelaws/${data.byelaw.master_id}`);
    } catch (err) {
      toast.error(getApiError(err, "Upload failed."));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <PageHeader title="Upload Bye-law" subtitle="Upload a PDF or Word document and capture its metadata." icon="bi-cloud-arrow-up" />

      <form onSubmit={handleSubmit} noValidate>
        <div className="row g-3">
          {/* File */}
          <div className="col-12 col-lg-5">
            <div className="app-card p-3 h-100">
              <h6 className="fw-bold mb-3"><i className="bi bi-file-earmark-arrow-up me-2 text-brand" />Document</h6>
              {!file ? (
                <div
                  className={`dropzone ${drag ? "drag" : ""} ${errors.file ? "border-danger" : ""}`}
                  onClick={() => fileInput.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={onDrop}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInput.current?.click()}
                >
                  <div className="dz-icon mb-2"><i className="bi bi-cloud-arrow-up" /></div>
                  <div className="fw-semibold">Drag &amp; drop your file here</div>
                  <div className="muted small">or click to browse · PDF, DOC, DOCX · max {MAX_MB} MB</div>
                </div>
              ) : (
                <div className="file-pill">
                  <span className="fp-icon"><i className="bi bi-file-earmark-text" /></span>
                  <div className="flex-grow-1 min-w-0">
                    <div className="fw-semibold text-truncate">{file.name}</div>
                    <div className="text-muted small">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                  </div>
                  {!uploading && <button type="button" className="btn btn-sm btn-light" onClick={() => setFile(null)}><i className="bi bi-x-lg" /></button>}
                </div>
              )}
              {errors.file && <div className="field-error mt-2">{errors.file}</div>}
              <input ref={fileInput} type="file" accept={ACCEPTED.join(",")} hidden onChange={(e) => pickFile(e.target.files?.[0])} />

              {uploading && (
                <div className="mt-3">
                  <div className="d-flex justify-content-between small mb-1"><span>Uploading…</span><span>{progress}%</span></div>
                  <div className="progress" style={{ height: 8 }}>
                    <div className="progress-bar bg-accent" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Metadata */}
          <div className="col-12 col-lg-7">
            <div className="app-card p-3">
              <h6 className="fw-bold mb-3"><i className="bi bi-card-list me-2 text-brand" />Society &amp; bye-law details</h6>
              <div className="row g-3">
                <Field col="col-12 col-md-6" label="Society name" required value={meta.society_name} onChange={(v) => set("society_name", v)} error={errors.society_name} />
                <Field col="col-12 col-md-6" label="Registration number" required value={meta.society_registration_no} onChange={(v) => set("society_registration_no", v)} error={errors.society_registration_no} />
                <Field col="col-12 col-md-6" label="Society type" value={meta.society_type} onChange={(v) => set("society_type", v)} placeholder="e.g. Urban Co-op Bank" />
                <Field col="col-12 col-md-6" label="Bye-law title" required value={meta.byelaw_title} onChange={(v) => set("byelaw_title", v)} error={errors.byelaw_title} />
                <Field col="col-12 col-md-6" label="Version / amendment no." required value={meta.byelaw_version} onChange={(v) => set("byelaw_version", v)} error={errors.byelaw_version} placeholder="e.g. 1.0" />
                <Field col="col-12 col-md-6" type="date" label="Effective date" value={meta.effective_date} onChange={(v) => set("effective_date", v)} />
                <Field col="col-12 col-md-6" label="Registrar approval no." value={meta.registrar_approval_no} onChange={(v) => set("registrar_approval_no", v)} />
                <Field col="col-12 col-md-6" type="date" label="Approval date" value={meta.approval_date} onChange={(v) => set("approval_date", v)} />
                <div className="col-12">
                  <label className="form-label">Remarks</label>
                  <textarea className="form-control" rows={2} value={meta.remarks} onChange={(e) => set("remarks", e.target.value)} placeholder="Optional notes" />
                </div>
              </div>
            </div>

            <div className="d-flex justify-content-end gap-2 mt-3">
              <button type="button" className="btn btn-light" onClick={() => navigate("/byelaws")} disabled={uploading}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={uploading}>
                {uploading ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="bi bi-cloud-arrow-up me-2" />}
                Upload bye-law
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

function Field({ col, label, required, value, onChange, error, type = "text", placeholder }) {
  return (
    <div className={col}>
      <label className="form-label">{label} {required && <span className="req">*</span>}</label>
      <input type={type} className={`form-control ${error ? "is-invalid" : ""}`} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
      {error && <div className="field-error">{error}</div>}
    </div>
  );
}
