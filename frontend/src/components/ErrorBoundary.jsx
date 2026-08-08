import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    if (import.meta.env.DEV) {
      console.error("ErrorBoundary caught:", error, errorInfo);
    }
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontFamily: "system-ui, sans-serif",
          textAlign: "center",
          padding: "2rem",
        }}
      >
        <h1>Something went wrong</h1>
        <p style={{ color: "#666", marginBottom: "1.5rem" }}>
          {this.state.error?.message || "An unexpected error occurred."}
        </p>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: "0.5rem 1rem",
            fontSize: "1rem",
            cursor: "pointer",
          }}
        >
          Reload App
        </button>
      </div>
    );
  }
}
