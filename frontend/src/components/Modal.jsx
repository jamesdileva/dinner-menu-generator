// Modal component for Add Meal form (audit §13.21).
// Renders a centered overlay with the same form fields as the AddMeal card,
// used when Add Meal is a header badge button instead of a persistent card.

export default function Modal({ title, open, onClose, children }) {
  if (!open) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 9999,
      }}
    >
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--bg-card)",
          borderRadius: "10px",
          padding: "20px",
          maxWidth: "480px",
          width: "90%",
          maxHeight: "80vh",
          overflow: "auto",
          boxShadow: "var(--shadow)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "20px" }}>{title}</h2>
          <button
            className="btn-sm"
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              fontSize: "18px",
              cursor: "pointer",
              color: "var(--text-muted)",
            }}
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
