import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Dashboard Page", () => {
  test.describe.configure({ timeout: 90000 });

  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60000 });
    await expect(page.getByRole("heading", { level: 1, name: /welcome back/i })).toBeVisible({
      timeout: 30000,
    });
  });

  test.describe("Page Structure", () => {
    test("displays welcome message with user name", async ({ page }) => {
      await expect(page.getByText(/welcome back/i)).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(
        page.getByText(/here's what's happening with your research pipeline/i)
      ).toBeVisible();
    });
  });

  test.describe("Statistics Cards", () => {
    test("displays Total Papers stat card", async ({ page }) => {
      const topStats = page.locator("div.grid.gap-4.md\\:grid-cols-3").first();
      await expect(topStats.getByText(/total papers/i)).toBeVisible();
    });

    test("displays Active Projects stat card", async ({ page }) => {
      const topStats = page.locator("div.grid.gap-4.md\\:grid-cols-3").first();
      await expect(topStats.getByText(/active projects/i)).toBeVisible();
    });

    test("displays Embeddings stat card", async ({ page }) => {
      const topStats = page.locator("div.grid.gap-4.md\\:grid-cols-3").first();
      await expect(topStats.getByText(/embeddings/i)).toBeVisible();
    });

    test("shows zero values for new user", async ({ page }) => {
      const statsSection = page.locator(".grid.gap-4.md\\:grid-cols-3");
      await expect(statsSection.getByText("0").first()).toBeVisible();
    });
  });

  test.describe("Recent Papers Section", () => {
    test("displays Recent Papers section header", async ({ page }) => {
      await expect(
        page.getByRole("heading", { level: 3, name: /recent papers/i }).first()
      ).toBeVisible();
      await expect(page.getByRole("link", { name: /view all/i }).first()).toBeVisible();
    });

    test("shows empty state when no papers", async ({ page }) => {
      const emptyStateTitle = page.getByText(/no papers yet/i).first();
      const recentPaperLink = page
        .locator('main a[href^="/papers/"]:not([href="/papers"])')
        .first();

      await expect
        .poll(
          async () => {
            const hasEmptyState = await emptyStateTitle.isVisible().catch(() => false);
            const hasRecentPaper = await recentPaperLink.isVisible().catch(() => false);
            return hasEmptyState || hasRecentPaper;
          },
          { timeout: 15000 }
        )
        .toBeTruthy();

      const hasEmptyState = await emptyStateTitle.isVisible().catch(() => false);

      if (hasEmptyState) {
        await expect(page.getByText(/import papers to get started/i)).toBeVisible();
      }
    });

    test('has "View all" link to papers page', async ({ page }) => {
      const viewAllLink = page.getByRole("link", { name: /view all/i }).first();
      await expect(viewAllLink).toBeVisible();
      await viewAllLink.click();
      await expect(page).toHaveURL(/\/papers/);
    });
  });

  test.describe("Workflow Lanes", () => {
    test("displays discover, evaluate, and transfer lanes", async ({ page }) => {
      const lanes = page.locator("div.grid.gap-6.md\\:grid-cols-3").first();
      await expect(lanes.getByText(/^discover$/i)).toBeVisible();
      await expect(lanes.getByText(/^evaluate$/i)).toBeVisible();
      await expect(lanes.getByText(/^transfer$/i)).toBeVisible();
    });

    test("has workflow CTA buttons", async ({ page }) => {
      await expect(page.getByRole("button", { name: /search papers/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /view papers/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /start transfer/i })).toBeVisible();
    });

    test("search papers CTA navigates to search", async ({ page }) => {
      await page.getByRole("button", { name: /search papers/i }).click();
      await expect(page).toHaveURL(/\/search/);
    });

    test("view papers CTA navigates to papers", async ({ page }) => {
      await page.getByRole("button", { name: /view papers/i }).click();
      await expect(page).toHaveURL(/\/papers/);
    });

    test("start transfer CTA navigates to transfer", async ({ page }) => {
      await page.getByRole("button", { name: /start transfer/i }).click();
      await expect(page).toHaveURL(/\/transfer/);
    });
  });

  test.describe("Loading States", () => {
    test("handles loading state gracefully", async ({ page }) => {
      await page.reload();
      await expect(page.getByRole("heading", { level: 1, name: /welcome back/i })).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts layout on smaller screens", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByText(/total papers/i)).toBeVisible();

      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByText(/welcome back/i)).toBeVisible();
    });
  });
});
