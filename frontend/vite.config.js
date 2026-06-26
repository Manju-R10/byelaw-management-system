import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on 5173 (allowed by the backend CORS configuration). A proxy is provided
// as a fallback so the client also works when VITE_API_BASE_URL is left relative.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
