import { defineConfig, devices } from "@playwright/test";

const channel = process.env.PLAYWRIGHT_CHROMIUM_CHANNEL;
const baseURL = process.env.GROUNDUP_WEB_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 45_000,
  use: { baseURL, channel, trace: "retain-on-failure", reducedMotion: "reduce" },
  webServer: process.env.GROUNDUP_WEB_URL ? undefined : {
    command: "npm run start",
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [
    { name: "desktop", testMatch: "**/*.desktop.spec.ts", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1024 } } },
    { name: "mobile", testMatch: "**/*.mobile.spec.ts", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
});
