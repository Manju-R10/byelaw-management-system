import { useEffect } from "react";

/** Lightweight, accessible modal with overlay. Closes on Escape and backdrop click. */
export default function Modal({ open, title, onClose, children, footer, size = "" }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose?.()} role="dialog" aria-modal="true">
      <div className={`modal-panel ${size}`}>
        <div className="modal-header-row">
          <h5>{title}</h5>
          <button className="icon-btn" onClick={onClose} aria-label="Close" style={{ width: 34, height: 34 }}>
            <i className="bi bi-x-lg" />
          </button>
        </div>
        <div className="modal-body-row">{children}</div>
        {footer && <div className="modal-footer-row">{footer}</div>}
      </div>
    </div>
  );
}
