import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

// Relative base so the bundle resolves wherever the preview is hosted.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist-preview",
    emptyOutDir: true,
    rollupOptions: { input: resolve(__dirname, "preview.html") },
  },
});
