import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { byelawApi } from "../../api/byelaws";
import { useAuth } from "../../context/AuthContext";
import { usePagedList } from "../../hooks/usePagedList";
import { useDebounce } from "../../hooks/useDebounce";
import PageHeader from "../../components/ui/PageHeader";
import Pagination from "../../components/ui/Pagination";
import StatusBadge from "../../components/ui/StatusBadge";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonLines } from "../../components/ui/Skeleton";
import { formatDate } from "../../utils/format";

const EXTRACTION_STATUSES = ["Pending", "Validated", "Processing", "Completed", "Failed", "Reviewed"];
const WORKFLOW_STATUSES = ["Draft", "Submitted", "Under Review", "Verified", "Approved", "Rejected", "Published"];

export default function ByelawsList() {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const canUpload = hasPermission("BYELAW_UPLOAD");

  const [search, setSearch] = useState("");
  const debounced = useDebounce(search, 350);
  const fetcher = useCallback((params) => byelawApi.list(params), []);
  const list = usePagedList(fetcher, { pageSize: 10 });

  useEffect(() => {
    list.setFilter("search", debounced);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced]);

  return (
    <div>
      <PageHeader
        title="Bye-laws"
        subtitle="Browse, open and manage digitized bye-law documents."
        icon="bi-journal-text"
        actions={canUpload && (
          <Link to="/byelaws/upload" className="btn btn-primary"><i className="bi bi-cloud-arrow-up me-2" />Upload bye-law</Link>
        )}
      />

      <div className="app-card">
        <div className="toolbar">
          <div className="search-box">
            <i className="bi bi-search" />
            <input className="form-control" placeholder="Search by society, registration no. or title…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="form-select" style={{ maxWidth: 180 }} value={list.filters.extraction_status || ""} onChange={(e) => list.setFilter("extraction_status", e.target.value || "")}>
            <option value="">All extraction</option>
            {EXTRACTION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="form-select" style={{ maxWidth: 180 }} value={list.filters.workflow_status || ""} onChange={(e) => list.setFilter("workflow_status", e.target.value || "")}>
            <option value="">All workflow</option>
            {WORKFLOW_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="table-responsive">
          {list.loading ? (
            <div className="p-3"><SkeletonLines rows={6} /></div>
          ) : list.error ? (
            <EmptyState icon="bi-exclamation-octagon" title="Couldn't load bye-laws" subtitle={list.error} />
          ) : list.items.length === 0 ? (
            <EmptyState icon="bi-journal" title="No bye-laws found" subtitle={canUpload ? "Upload a bye-law document to get started." : "Nothing matches your filters."} />
          ) : (
            <table className="table table-hover align-middle mb-0">
              <thead>
                <tr><th>Society</th><th>Title</th><th>Version</th><th>Extraction</th><th>Workflow</th><th>Uploaded</th><th></th></tr>
              </thead>
              <tbody>
                {list.items.map((b) => (
                  <tr key={b.master_id} className="cursor-pointer" onClick={() => navigate(`/byelaws/${b.master_id}`)}>
                    <td>
                      <div className="fw-semibold d-flex align-items-center gap-2">
                        {b.society_name}
                        {b.is_active && <span className="status-badge" style={{ background: "#d1fae5", color: "#047857" }}><span className="dot" />Active</span>}
                      </div>
                      <div className="text-muted small">{b.society_registration_no}</div>
                    </td>
                    <td>{b.byelaw_title}</td>
                    <td>{b.byelaw_version}</td>
                    <td><StatusBadge status={b.extraction_status} /></td>
                    <td><StatusBadge status={b.workflow_status} /></td>
                    <td className="text-muted small">{formatDate(b.uploaded_date)}</td>
                    <td className="text-end"><i className="bi bi-chevron-right text-muted" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {!list.loading && <Pagination page={list.page} totalPages={list.totalPages} total={list.total} pageSize={list.pageSize} onChange={list.setPage} />}
      </div>
    </div>
  );
}
