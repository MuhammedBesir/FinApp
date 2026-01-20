/**
 * Main Entry Point
 */
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { ThemeProvider } from "./context/ThemeContext";
import ErrorBoundary from "./components/Common/ErrorBoundary";
import "./index.css";
import axios from "axios";

// Debug Environment and Safety Fix
console.log("App Version: 1.0.1 - Env Check:", {
  MODE: import.meta.env.MODE,
  API_URL: import.meta.env.VITE_API_URL,
  WS_URL: import.meta.env.VITE_WS_URL
});

// Force fix: If we are in production but API_URL is localhost, force it to relative
if (!window.location.hostname.includes('localhost') && import.meta.env.VITE_API_URL?.includes('localhost')) {
  console.warn("⚠️ Detected localhost API URL in production. Forcing relative path.");
  // We do NOT set axios.defaults.baseURL globally to avoid double prefixing (e.g. /api/api/...)
  // Instead, we rely on individual services to handle the base URL correctly.
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
