import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testMatch: /scaffold\.spec\.ts/,
  outputDir: "test-results-scaffold",
  use: { baseURL: "http://127.0.0.1:5177" },
  webServer: {
    command:
      "npm run dev -- --mode live --host 127.0.0.1 --port 5177 --strictPort",
    url: "http://127.0.0.1:5177",
    env: { VITE_MOCK: "0", VITE_API_URL: "/api" },
    reuseExistingServer: false,
  },
  projects: [
    { name: "phone", use: { viewport: { width: 375, height: 812 } } },
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    { name: "projector", use: { viewport: { width: 1920, height: 1080 } } },
  ],
});
