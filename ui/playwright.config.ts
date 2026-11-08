import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testIgnore: [/live\.spec\.ts/, /scaffold\.spec\.ts/],
  use: { baseURL: "http://127.0.0.1:5174" },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5174 --strictPort",
    url: "http://127.0.0.1:5174",
    env: { VITE_MOCK: "1", VITE_API_URL: "http://127.0.0.1:18000" },
    reuseExistingServer: false,
  },
  projects: [
    { name: "phone", use: { viewport: { width: 375, height: 812 } } },
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    { name: "projector", use: { viewport: { width: 1920, height: 1080 } } },
  ],
});
