/**
 * Role-based navigation. Items are filtered by the current user's permissions.
 * `ready: false` marks pages delivered in later frontend phases — they render a
 * "Coming soon" placeholder so the sidebar is complete and links are never dead.
 */
export const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [
      { label: "Dashboard", to: "/dashboard", icon: "bi-speedometer2", ready: true },
      { label: "Notifications", to: "/notifications", icon: "bi-bell", ready: true },
    ],
  },
  {
    label: "Bye-laws",
    items: [
      { label: "All Bye-laws", to: "/byelaws", icon: "bi-journal-text", permission: "BYELAW_SEARCH", ready: true },
      { label: "Upload", to: "/byelaws/upload", icon: "bi-cloud-arrow-up", permission: "BYELAW_UPLOAD", ready: true },
      { label: "Search", to: "/search", icon: "bi-search", permission: "BYELAW_SEARCH", ready: true },
      { label: "Approvals", to: "/approvals", icon: "bi-check2-square", permission: "BYELAW_VERIFY", ready: true },
    ],
  },
  {
    label: "Administration",
    items: [
      { label: "Users", to: "/users", icon: "bi-people", permission: "USER_READ", ready: true },
      { label: "Roles & Permissions", to: "/roles", icon: "bi-shield-lock", permission: "ROLE_READ", ready: true },
      { label: "Audit Log", to: "/audit", icon: "bi-clipboard-data", permission: "AUDIT_VIEW", ready: false },
    ],
  },
];

/** Flattened, permission-filtered nav for the current user. */
export function getVisibleSections(hasPermission) {
  return NAV_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((i) => !i.permission || hasPermission(i.permission)),
  })).filter((section) => section.items.length > 0);
}
