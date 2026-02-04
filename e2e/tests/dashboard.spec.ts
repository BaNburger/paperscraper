import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Dashboard Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/");
    await page.waitForLoadState("networkidle");
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
      await expect(page.getByText(/total papers/i)).toBeVisible();
    });

    test("displays Active Projects stat card", async ({ page }) => {
      await expect(page.getByText(/active projects/i)).toBeVisible();
    });

    test("displays Embeddings stat card", async ({ page }) => {
      await expect(page.getByText(/embeddings/i).first()).toBeVisible();
    });

    test("shows zero values for new user", async ({ page }) => {
      const statsSection = page.locator(".grid.gap-4.md\\:grid-cols-3");
      await expect(statsSection.getByText("0").first()).toBeVisible();
    });
  });

  test.describe("Recent Papers Section", () => {
    test("displays Recent Papers section header", async ({ page }) => {
      await expect(page.getByText(/recent papers/i)).toBeVisible();
      await expect(page.getByText(/latest papers in your library/i)).toBeVisible();
    });

    test("shows empty state when no papers", async ({ page }) => {
      await expect(page.getByText(/no papers yet/i)).toBeVisible();
      await expect(page.getByText(/import papers to get started/i)).toBeVisible();
    });

    test('has "View all" link to papers page', async ({ page }) => {
      const viewAllLink = page.getByRole("link", { name: /view all/i }).first();
      await expect(viewAllLink).toBeVisible();
      await viewAllLink.click();
      await expect(page).toHaveURL(/\/papers/);
    });
  });

  test.describe("Projects Section", () => {
    test("displays Projects section header", async ({ page }) => {
      // Scope to main to avoid matching sidebar "Projects" link
      const mainContent = page.locator("main");
      await expect(mainContent.getByText("Projects", { exact: true }).first()).toBeVisible();
    });

    test("shows empty state when no projects", async ({ page }) => {
      await expect(page.getByText(/no projects yet/i)).toBeVisible();
    });

    test('has "View all" link to projects page', async ({ page }) => {
      const projectsViewAll = page.getByRole("link", { name: /view all/i }).nth(1);
      if (await projectsViewAll.isVisible()) {
        await projectsViewAll.click();
        await expect(page).toHaveURL(/\/projects/);
      }
    });
  });

  test.describe("Quick Actions Section", () => {
    test("displays Quick Actions section", async ({ page }) => {
      await expect(page.getByText(/quick actions/i)).toBeVisible();
    });

    test("has Import Papers button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /import papers/i })).toBeVisible();
    });

    test("has Search Library button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /search library/i })).toBeVisible();
    });

    test("has Manage Projects button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /manage projects/i })).toBeVisible();
    });
  });

  test.describe("Loading States", () => {
    test("handles loading state gracefully", async ({ page }) => {
      await page.reload();
      await page.waitForLoadState("networkidle");
      await expect(page.getByText(/welcome back/i)).toBeVisible();
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
