import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for Paper Scraper E2E tests.
 * Covers all browsers (Chromium, Firefox, WebKit) across
 * desktop, tablet, and mobile viewports.
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: "./e2e/tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html", { open: "never" }],
    ["list"],
    ...(process.env.CI ? [["github"] as const] : []),
  ],

  use: {
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "on-first-retry",
  },

  projects: [
    // =========================================================================
    // Desktop Browsers
    // =========================================================================
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox-desktop",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit-desktop",
      use: { ...devices["Desktop Safari"] },
    },

    // =========================================================================
    // Tablet Viewports
    // =========================================================================
    {
      name: "chromium-tablet",
      use: {
        ...devices["iPad Pro 11"],
        // iPad Pro 11 is 834x1194 in portrait
      },
    },
    {
      name: "chromium-tablet-landscape",
      use: {
        ...devices["iPad Pro 11 landscape"],
      },
    },
    {
      name: "firefox-tablet",
      use: {
        browserName: "firefox",
        viewport: { width: 768, height: 1024 },
        deviceScaleFactor: 2,
        isMobile: false,
        hasTouch: true,
      },
    },
    {
      name: "webkit-tablet",
      use: {
        ...devices["iPad Mini"],
      },
    },

    // =========================================================================
    // Mobile Viewports
    // =========================================================================
    {
      name: "chromium-mobile",
      use: {
        ...devices["Pixel 7"],
      },
    },
    {
      name: "chromium-mobile-landscape",
      use: {
        ...devices["Pixel 7 landscape"],
      },
    },
    {
      name: "webkit-mobile",
      use: {
        ...devices["iPhone 14 Pro"],
      },
    },
    {
      name: "webkit-mobile-landscape",
      use: {
        ...devices["iPhone 14 Pro landscape"],
      },
    },
    {
      name: "firefox-mobile",
      use: {
        browserName: "firefox",
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true,
      },
    },

    // =========================================================================
    // Edge Cases / Additional Devices
    // =========================================================================
    {
      name: "chromium-small-mobile",
      use: {
        ...devices["iPhone SE"],
      },
    },
    {
      name: "chromium-large-desktop",
      use: {
        browserName: "chromium",
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 1,
      },
    },
  ],

  // Global timeout settings
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
});
