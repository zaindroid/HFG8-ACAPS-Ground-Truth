import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// The engine serves its business routes under /api and the built UI at the root, so the prefix is
// kept rather than stripped. Dev and production then address the API identically.
const proxy = {
  "/api": {
    target: "http://127.0.0.1:18000",
    changeOrigin: true,
  },
};
export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
