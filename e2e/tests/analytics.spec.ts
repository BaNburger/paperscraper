import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Analytics Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await page.waitForSelector('[data-testid="analytics-page"]', { timeout: 15000 });
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByTestId("analytics-heading")).toBeVisible();
      await expect(page.getByTestId("analytics-subtitle")).toBeVisible();
    });

    test("displays export buttons", async ({ page }) => {
      await expect(page.getByTestId("analytics-export-csv")).toBeVisible();
      await expect(page.getByTestId("analytics-export-bibtex")).toBeVisible();
    });
  });

  test.describe("Summary Statistics Cards", () => {
    test("displays all summary cards", async ({ page }) => {
      await expect(page.getByTestId("analytics-card-total-papers")).toBeVisible();
      await expect(page.getByTestId("analytics-card-scored-papers")).toBeVisible();
      await expect(page.getByTestId("analytics-card-projects")).toBeVisible();
      await expect(page.getByTestId("analytics-card-team-members")).toBeVisible();
    });

    test("shows zero values for new organization", async ({ page }) => {
      await expect(page.getByTestId("analytics-card-total-papers").getByText(/^0$/).first()).toBeVisible();
    });
  });

  test.describe("Charts Section", () => {
    test("displays all overview charts", async ({ page }) => {
      await expect(page.getByTestId("analytics-chart-import-trend")).toBeVisible();
      await expect(page.getByTestId("analytics-chart-papers-source")).toBeVisible();
      await expect(page.getByTestId("analytics-chart-score-distribution")).toBeVisible();
      await expect(page.getByTestId("analytics-chart-average-scores")).toBeVisible();
    });
  });

  test.describe("Top Papers Section", () => {
    test("displays top papers section", async ({ page }) => {
      await expect(page.getByTestId("analytics-top-papers")).toBeVisible();
    });

    test("has View all link", async ({ page }) => {
      const viewAllLink = page.getByTestId("analytics-view-all-papers");
      if (await viewAllLink.isVisible()) {
        await viewAllLink.click();
        await expect(page).toHaveURL(/\/papers/);
      }
    });
  });

  test.describe("Embedding Coverage Section", () => {
    test("displays embedding coverage and progress bar", async ({ page }) => {
      await expect(page.getByTestId("analytics-embedding-coverage")).toBeVisible();
      const progressTrack = page.getByTestId("analytics-embedding-progress-track");
      await expect(progressTrack).toBeVisible();
      await expect(page.getByTestId("analytics-embedding-progress-fill")).toHaveAttribute(
        "style",
        /width:\s*\d+(\.\d+)?%/
      );
      await expect(page.getByTestId("analytics-embedding-percent")).toBeVisible();
    });
  });

  test.describe("Export Functionality", () => {
    test("export buttons are enabled", async ({ page }) => {
      await expect(page.getByTestId("analytics-export-csv")).toBeEnabled();
      await expect(page.getByTestId("analytics-export-bibtex")).toBeEnabled();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByTestId("analytics-heading")).toBeVisible();
      await expect(page.getByTestId("analytics-card-total-papers")).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByTestId("analytics-heading")).toBeVisible();
    });
  });
});
