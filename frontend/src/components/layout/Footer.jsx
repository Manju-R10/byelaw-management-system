export default function Footer() {
  return (
    <footer className="app-footer">
      <span>
        © {new Date().getFullYear()} Centre for Development of Imaging Technology (C-DIT), Government of Kerala.
      </span>
      <span className="d-none d-md-inline">
        Cooperative Society Bye-law Digitization &amp; Clause Management System · v1.0.0
      </span>
    </footer>
  );
}
