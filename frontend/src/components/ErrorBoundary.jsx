import { Component } from "react";

/** Catches render-time errors anywhere in the tree and shows a recovery screen. */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error("Unhandled UI error:", error, info);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.assign("/dashboard");
  };

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="d-flex flex-column align-items-center justify-content-center text-center vh-100 p-4">
        <div className="mb-3 d-grid" style={{ width: 80, height: 80, placeItems: "center", borderRadius: 20, background: "#fee2e2", color: "#b91c1c", fontSize: "2.2rem" }}>
          <i className="bi bi-bug" />
        </div>
        <h3 className="fw-bold">Something went wrong</h3>
        <p className="muted" style={{ maxWidth: 440 }}>
          An unexpected error occurred while rendering this screen. You can return to the dashboard and try again.
        </p>
        <button className="btn btn-primary mt-2" onClick={this.handleReload}>
          <i className="bi bi-house-door me-2" />Back to Dashboard
        </button>
      </div>
    );
  }
}
