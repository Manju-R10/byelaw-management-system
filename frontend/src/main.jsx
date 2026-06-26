import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Bootstrap (CSS + JS bundle for dropdowns/collapse) and icons, then our theme last.
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import "bootstrap-icons/font/bootstrap-icons.css";
import "react-toastify/dist/ReactToastify.css";
import "./index.css";

import App from "./App";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
