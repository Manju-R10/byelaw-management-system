/**
 * Client-side clause-tree operations for the review screen.
 *
 * The tree is the nested structure returned by GET /byelaws/{id}/clauses (each node
 * has a `children` array). Structural edits mutate a cloned tree, then `flattenForReorder`
 * produces the payload for POST /byelaws/{id}/clauses/reorder — assigning a fresh
 * DFS pre-order `display_order`, the correct `parent_clause_id`, and a depth-based
 * `clause_level`. This keeps numbering/levels consistent after any move.
 */

export function cloneTree(roots) {
  return roots.map((n) => ({ ...n, children: cloneTree(n.children || []) }));
}

/** Locate a node and the sibling array that contains it. */
function locate(roots, clauseId, parent = null) {
  for (let i = 0; i < roots.length; i++) {
    const node = roots[i];
    if (node.clause_id === clauseId) return { node, siblings: roots, index: i, parent };
    const found = locate(node.children || [], clauseId, node);
    if (found) return found;
  }
  return null;
}

export function moveUp(roots, clauseId) {
  const tree = cloneTree(roots);
  const loc = locate(tree, clauseId);
  if (loc && loc.index > 0) {
    [loc.siblings[loc.index - 1], loc.siblings[loc.index]] = [loc.siblings[loc.index], loc.siblings[loc.index - 1]];
  }
  return tree;
}

export function moveDown(roots, clauseId) {
  const tree = cloneTree(roots);
  const loc = locate(tree, clauseId);
  if (loc && loc.index < loc.siblings.length - 1) {
    [loc.siblings[loc.index + 1], loc.siblings[loc.index]] = [loc.siblings[loc.index], loc.siblings[loc.index + 1]];
  }
  return tree;
}

/** Make a node a child of its immediately-preceding sibling. */
export function indent(roots, clauseId) {
  const tree = cloneTree(roots);
  const loc = locate(tree, clauseId);
  if (loc && loc.index > 0) {
    const [moved] = loc.siblings.splice(loc.index, 1);
    const newParent = loc.siblings[loc.index - 1];
    newParent.children = newParent.children || [];
    newParent.children.push(moved);
  }
  return tree;
}

/** Make a node a sibling of its parent (placed just after the parent). */
export function outdent(roots, clauseId) {
  const tree = cloneTree(roots);
  const loc = locate(tree, clauseId);
  if (loc && loc.parent) {
    const grand = locate(tree, loc.parent.clause_id);
    if (grand) {
      const [moved] = loc.siblings.splice(loc.index, 1);
      grand.siblings.splice(grand.index + 1, 0, moved);
    }
  }
  return tree;
}

export function canIndent(roots, clauseId) {
  const loc = locate(roots, clauseId);
  return !!loc && loc.index > 0;
}

export function canOutdent(roots, clauseId) {
  const loc = locate(roots, clauseId);
  return !!loc && !!loc.parent;
}

/** Produce the reorder payload (DFS pre-order). */
export function flattenForReorder(roots) {
  const items = [];
  let order = 0;
  const walk = (nodes, parentId, depth) => {
    for (const node of nodes) {
      order += 1;
      items.push({
        clause_id: node.clause_id,
        parent_clause_id: parentId,
        display_order: order,
        clause_level: Math.min(depth + 1, 6),
      });
      walk(node.children || [], node.clause_id, depth + 1);
    }
  };
  walk(roots, null, 0);
  return items;
}

export function countNodes(roots) {
  return roots.reduce((acc, n) => acc + 1 + countNodes(n.children || []), 0);
}
