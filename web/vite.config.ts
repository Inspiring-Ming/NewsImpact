// Dev server proxies the API, so the website and API behave as one site (as in production).
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/v1": "http://localhost:8000", "/health": "http://localhost:8000" } },
});
