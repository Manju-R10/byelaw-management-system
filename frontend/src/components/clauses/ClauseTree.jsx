import { useState } from "react";

/**
 * Recursive clause tree with expand/collapse. In `editable` mode each node shows
 * review controls (edit, add child, delete, move up/down, indent/outdent). All
 * mutations are delegated to the parent via callbacks.
 */
export default function ClauseTree({ nodes, editable = false, handlers = {}, highlightId }) {
  const [collapsed, setCollapsed] = useState(() => new Set());

  const toggle = (id) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const expandAll = () => setCollapsed(new Set());
  const collapseAll = () => setCollapsed(new Set(collectIds(nodes)));

  if (!nodes || nodes.length === 0) return null;

  return (
    <div>
      <div className="d-flex justify-content-end gap-2 mb-2">
        <button className="btn btn-sm btn-light" onClick={expandAll}><i className="bi bi-arrows-expand me-1" />Expand all</button>
        <button className="btn btn-sm btn-light" onClick={collapseAll}><i className="bi bi-arrows-collapse me-1" />Collapse all</button>
      </div>
      <div className="clause-tree">
        {nodes.map((node, i) => (
          <Node
            key={node.clause_id}
            node={node}
            index={i}
            siblingCount={nodes.length}
            depth={0}
            collapsed={collapsed}
            toggle={toggle}
            editable={editable}
            handlers={handlers}
            highlightId={highlightId}
          />
        ))}
      </div>
    </div>
  );
}

function Node({ node, index, siblingCount, depth, collapsed, toggle, editable, handlers, highlightId }) {
  const children = node.children || [];
  const hasChildren = children.length > 0;
  const isCollapsed = collapsed.has(node.clause_id);
  const isHighlight = highlightId === node.clause_id;

  return (
    <div className="clause-node" style={isHighlight ? { borderColor: "#1e3a8a", boxShadow: "0 0 0 2px rgba(30,58,138,0.15)" } : undefined}>
      <div className="clause-node-head">
        <span className="caret" onClick={() => hasChildren && toggle(node.clause_id)} role={hasChildren ? "button" : undefined} aria-label="Toggle">
          {hasChildren ? <i className={`bi ${isCollapsed ? "bi-caret-right-fill" : "bi-caret-down-fill"}`} /> : <i className="bi bi-dot" />}
        </span>
        {(node.chapter_no || node.clause_no) && <span className="clause-no-pill">{node.chapter_no || node.clause_no}</span>}
        <span className="clause-lvl">L{node.clause_level}</span>
        <span className="fw-semibold text-truncate" title={node.clause_title || node.clause_text}>
          {node.clause_title || node.clause_text?.slice(0, 90) || "(untitled)"}
        </span>

        {editable && (
          <div className="clause-actions">
            <button className="btn btn-light" title="Move up" disabled={index === 0} onClick={() => handlers.onMove?.(node.clause_id, "up")}><i className="bi bi-arrow-up" /></button>
            <button className="btn btn-light" title="Move down" disabled={index === siblingCount - 1} onClick={() => handlers.onMove?.(node.clause_id, "down")}><i className="bi bi-arrow-down" /></button>
            <button className="btn btn-light" title="Indent (make child of previous)" disabled={index === 0} onClick={() => handlers.onMove?.(node.clause_id, "indent")}><i className="bi bi-text-indent-left" /></button>
            <button className="btn btn-light" title="Outdent" disabled={depth === 0} onClick={() => handlers.onMove?.(node.clause_id, "outdent")}><i className="bi bi-text-indent-right" /></button>
            <button className="btn btn-outline-secondary" title="Add sub-clause" onClick={() => handlers.onAddChild?.(node)}><i className="bi bi-plus-lg" /></button>
            <button className="btn btn-outline-secondary" title="Edit" onClick={() => handlers.onEdit?.(node)}><i className="bi bi-pencil" /></button>
            <button className="btn btn-outline-danger" title="Delete (with sub-clauses)" onClick={() => handlers.onDelete?.(node)}><i className="bi bi-trash" /></button>
          </div>
        )}
      </div>

      {!isCollapsed && node.clause_text && node.clause_title && (
        <div className="clause-body-text">{node.clause_text}</div>
      )}

      {!isCollapsed && hasChildren && (
        <div className="clause-children">
          {children.map((child, i) => (
            <Node
              key={child.clause_id}
              node={child}
              index={i}
              siblingCount={children.length}
              depth={depth + 1}
              collapsed={collapsed}
              toggle={toggle}
              editable={editable}
              handlers={handlers}
              highlightId={highlightId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function collectIds(nodes) {
  const ids = [];
  const walk = (ns) => ns.forEach((n) => { if ((n.children || []).length) { ids.push(n.clause_id); walk(n.children); } });
  walk(nodes);
  return ids;
}
