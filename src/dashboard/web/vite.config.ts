import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build the static bundle into ../api/static so server.py serves it same-origin.
// `base: './'` keeps asset URLs relative. In dev, proxy /api to the Python server.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "../api/static", emptyOutDir: true },
  server: {
    proxy: {
      "/api": "http://localhost:8888",
      "/health": "http://localhost:8888",
    },
  },
});
