import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Analytics Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /analytics/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(
        page.getByText(/insights (and metrics|into) for your research pipeline/i)
      ).toBeVisible();
    });

    test("displays export buttons", async ({ page }) => {
      await expect(page.getByRole("button", { name: /export csv/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /export bibtex/i })).toBeVisible();
    });
  });

  test.describe("Summary Statistics Cards", () => {
    test("displays Total Papers card", async ({ page }) => {
      await expect(page.getByText(/total papers/i).first()).toBeVisible();
    });

    test("displays Scored Papers card", async ({ page }) => {
      await expect(page.getByText(/scored papers/i).first()).toBeVisible();
    });

    test("displays Projects card", async ({ page }) => {
      await expect(page.getByText("Projects").first()).toBeVisible();
    });

    test("displays Team Members card", async ({ page }) => {
      await expect(page.getByText(/team members/i).first()).toBeVisible();
    });

    test("shows zero values for new organization", async ({ page }) => {
      // New org should have 0 papers
      const statsSection = page.locator(".grid.gap-4");
      await expect(statsSection.getByText("0").first()).toBeVisible();
    });
  });

  test.describe("Charts Section", () => {
    test("displays Import Trend chart", async ({ page }) => {
      await expect(page.getByText(/import trend/i)).toBeVisible();
      await expect(
        page.getByText(/(papers imported over the last 30 days|papers added over time)/i)
      ).toBeVisible();
    });

    test("displays Papers by Source chart", async ({ page }) => {
      await expect(page.getByText(/papers by source/i)).toBeVisible();
      await expect(
        page.getByText(/(distribution of papers by import source|where your papers come from)/i)
      ).toBeVisible();
    });

    test("displays Score Distribution chart", async ({ page }) => {
      await expect(page.getByText(/score distribution/i)).toBeVisible();
    });

    test("displays Average Scores by Dimension chart", async ({ page }) => {
      await expect(page.getByText(/average scores by dimension/i)).toBeVisible();
    });
  });

  test.describe("Top Papers Section", () => {
    test("displays Top Scored Papers section", async ({ page }) => {
      await expect(page.getByText(/top scored papers/i)).toBeVisible();
    });

    test("shows empty state when no papers", async ({ page }) => {
      await expect(page.getByText(/no papers yet/i)).toBeVisible();
    });

    test("has View all link", async ({ page }) => {
      const viewAllLink = page.getByRole("button", { name: /view all/i });
      if (await viewAllLink.isVisible()) {
        await viewAllLink.click();
        await expect(page).toHaveURL(/\/papers/);
      }
    });
  });

  test.describe("Embedding Coverage Section", () => {
    test("displays Embedding Coverage section", async ({ page }) => {
      await expect(page.getByText(/embedding coverage/i)).toBeVisible();
    });

    test("displays coverage description", async ({ page }) => {
      await expect(
        page.getByText(/(percentage of papers with generated embeddings|papers with vector embeddings)/i)
      ).toBeVisible();
    });

    test("shows progress bar", async ({ page }) => {
      const progressTrack = page.locator(".h-4.bg-muted.rounded-full.overflow-hidden");
      await expect(progressTrack).toBeVisible();
      const progressFill = progressTrack.locator("> div").first();
      await expect(progressFill).toHaveAttribute("style", /width:\s*\d+(\.\d+)?%/);
    });
  });

  test.describe("Export Functionality", () => {
    test("CSV export button is clickable", async ({ page }) => {
      const csvButton = page.getByRole("button", { name: /export csv/i });
      await expect(csvButton).toBeEnabled();
    });

    test("BibTeX export button is clickable", async ({ page }) => {
      const bibtexButton = page.getByRole("button", { name: /export bibtex/i });
      await expect(bibtexButton).toBeEnabled();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /analytics/i })).toBeVisible();
      await expect(page.getByText(/total papers/i).first()).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /analytics/i })).toBeVisible();
    });
  });
});
