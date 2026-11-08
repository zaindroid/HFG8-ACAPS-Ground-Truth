import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Minimal standalone config. The original Figma Make config depends on Make-only files.
export default defineConfig({
  plugins: [react(), tailwindcss()],
});
