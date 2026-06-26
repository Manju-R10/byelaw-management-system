import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { byelawApi } from "../../api/byelaws";
import { getApiError } from "../../api/client";
import { usePagedList } from "../../hooks/usePagedList";
import PageHeader from "../../components/ui/PageHeader";
import Pagination from "../../components/ui/Pagination";
import StatusBadge from "../../components/ui/StatusBadge";
import EmptyState from "../../components/ui/EmptyState";
import { SkeletonLines } from "../../components/ui/Skeleton";
import WorkflowActions from "../../components/workflow/WorkflowActions";
import { formatDate } from "../../utils/format";

const QUEUES = [
  { key: "Submitted", label: "Submitted", icon: "bi-inbox" },
  { key: "Under Review", label: "Under Review", icon: "bi-clipboard-check" },
  { key: "Verified", label: "Verified", icon: "bi-check2-circle" },
  { key: "Approved", label: "Approved", icon: "bi-patch-check" },
  { key: "Rejected", label: "Rejected", icon: "bi-x-octagon" },
];

export default function Approvals() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState("Submitted");
  const fetcher = useCallback((params) => byelawApi.list(params), []);
  const list = usePagedList(fetcher, { pageSize: 10, initialFilters: { workflow_status: "Submitted" } });
  const [counts, setCounts] = useState({});

  useEffect(() => {
    list.setFilter("workflow_status", queue);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queue]);

  // Lightweight per-queue counts for the tab badges.
  useEffect(() => {
    let active = true;
    Promise.all(
      QUEUES.map((q) => byelawApi.list({ page_size: 1, workflow_status: q.key }).then((r) => [q.key, r.data.total]).catch(() => [q.key, 0]))
    ).then((entries) => { if (active) setCounts(Object.fromEntries(entries)); });
    return () => { active = false; };
  }, [list.items]);

  return (
    <div>
      <PageHeader title="Approvals" subtitle="Review, verify, approve and publish bye-laws awaiting action." icon="bi-check2-square" />

      <div className="app-card">
        <div className="app-tabs px-2 pt-1" style={{ overflowX: "auto" }}>
          {QUEUES.map((q) => (
            <button key={q.key} className={`app-tab ${queue === q.key ? "active" : ""}`} onClick={() => setQueue(q.key)} style={{ whiteSpace: "nowrap" }}>
              <i className={`bi ${q.icon} me-2`} />{q.label}
              {counts[q.key] > 0 && <span className="badge bg-accent ms-2">{counts[q.key]}</span>}
            </button>
          ))}
        </div>

        <div className="table-responsive">
          {list.loading ? (
            <div className="p-3"><SkeletonLines rows={5} /></div>
          ) : list.error ? (
            <EmptyState icon="bi-exclamation-octagon" title="Couldn't load queue" subtitle={list.error} />
          ) : list.items.length === 0 ? (
            <EmptyState icon="bi-check2-circle" title={`Nothing in "${queue}"`} subtitle="This queue is currently empty." />
          ) : (
            <table className="table table-hover align-middle mb-0">
              <thead>
                <tr><th>Society</th><th>Title</th><th>Version</th><th>Extraction</th><th>Uploaded</th><th className="text-end">Actions</th></tr>
              </thead>
              <tbody>
                {list.items.map((b) => (
                  <tr key={b.master_id}>
                    <td className="fw-semibold cursor-pointer" onClick={() => navigate(`/byelaws/${b.master_id}`)}>
                      {b.society_name}<div className="text-muted small">{b.society_registration_no}</div>
                    </td>
                    <td className="cursor-pointer" onClick={() => navigate(`/byelaws/${b.master_id}`)}>{b.byelaw_title}</td>
                    <td>{b.byelaw_version}</td>
                    <td><StatusBadge status={b.extraction_status} /></td>
                    <td className="text-muted small">{formatDate(b.uploaded_date)}</td>
                    <td>
                      <div className="d-flex justify-content-end align-items-center gap-2">
                        <WorkflowActions masterId={b.master_id} status={b.workflow_status} onDone={list.reload} size="btn-sm" />
                        <button className="btn btn-sm btn-outline-secondary" onClick={() => navigate(`/byelaws/${b.master_id}`)} title="Open"><i className="bi bi-box-arrow-up-right" /></button>
                      </div>
                    </td>
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
