import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Navigation & Layout", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
  });

  test.describe("Sidebar Navigation", () => {
    test("displays all main navigation links", async ({ page }) => {
      // Scope to aside to avoid matching dashboard quick action links
      const sidebar = page.locator("aside");
      await expect(sidebar).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /dashboard/i })).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /papers/i })).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /projects/i })).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /search/i })).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /analytics/i })).toBeVisible();
    });

    test("displays bottom navigation links", async ({ page }) => {
      const sidebar = page.locator("aside");
      await expect(sidebar.getByRole("link", { name: /team/i })).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /settings/i })).toBeVisible();
    });

    test("navigates to Papers page", async ({ page }) => {
      const sidebar = page.locator("aside");
      await sidebar.getByRole("link", { name: /papers/i }).click();
      await expect(page).toHaveURL(/\/papers/);
      await expect(page.getByRole("heading", { level: 1, name: /papers/i })).toBeVisible();
    });

    test("navigates to Projects page", async ({ page }) => {
      const sidebar = page.locator("aside");
      await sidebar.getByRole("link", { name: /projects/i }).click();
      await expect(page).toHaveURL(/\/projects/);
      await expect(page.getByRole("heading", { level: 1, name: /projects/i })).toBeVisible();
    });

    test("navigates to Search page", async ({ page }) => {
      const sidebar = page.locator("aside");
      await sidebar.getByRole("link", { name: /search/i }).click();
      await expect(page).toHaveURL(/\/search/);
      await expect(page.getByRole("heading", { level: 1, name: /search/i })).toBeVisible();
    });

    test("navigates to Analytics page", async ({ page }) => {
      const sidebar = page.locator("aside");
      await sidebar.getByRole("link", { name: /analytics/i }).click();
      await expect(page).toHaveURL(/\/analytics/);
    });

    test("navigates to Team page", async ({ page }) => {
      const sidebar = page.locator("aside");
      await sidebar.getByRole("link", { name: /team/i }).click();
      await expect(page).toHaveURL(/\/team/);
    });

    test("navigates to Settings page", async ({ page }) => {
      const sidebar = page.locator("aside");
      await sidebar.getByRole("link", { name: /settings/i }).click();
      await expect(page).toHaveURL(/\/settings/);
      await expect(page.getByRole("heading", { level: 1, name: /settings/i })).toBeVisible();
    });

    test("highlights active navigation item", async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("networkidle");

      const sidebar = page.locator("aside");
      await expect(sidebar.getByRole("link", { name: /dashboard/i })).toHaveClass(/bg-primary/);

      await sidebar.getByRole("link", { name: /papers/i }).click();
      await expect(page).toHaveURL(/\/papers/);
      await expect(sidebar.getByRole("link", { name: /papers/i })).toHaveClass(/bg-primary/);
    });

    test("can collapse and expand sidebar", async ({ page }) => {
      const collapseButton = page.getByRole("button", { name: /collapse sidebar/i });

      if (await collapseButton.isVisible()) {
        await collapseButton.click();

        const sidebar = page.locator("aside");
        await expect(sidebar).toHaveClass(/w-16/);

        await page.getByRole("button", { name: /expand sidebar/i }).click();
        await expect(sidebar).toHaveClass(/w-64/);
      }
    });
  });

  test.describe("Responsive Behavior", () => {
    test("hides sidebar on mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.locator("aside")).toBeHidden();
    });

    test("shows sidebar on desktop viewport", async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 800 });
      await expect(page.locator("aside")).toBeVisible();
    });
  });

  test.describe("Navbar", () => {
    test("displays user information or menu", async ({ page }) => {
      await expect(page.locator("header, nav").first()).toBeVisible();
    });
  });

  test.describe("Protected Routes", () => {
    test("redirects to login when accessing protected route while logged out", async ({
      browser,
    }) => {
      const context = await browser.newContext();
      const newPage = await context.newPage();

      await newPage.goto("/dashboard");
      await expect(newPage).toHaveURL(/\/login/);

      await newPage.goto("/papers");
      await expect(newPage).toHaveURL(/\/login/);

      await newPage.goto("/projects");
      await expect(newPage).toHaveURL(/\/login/);

      await context.close();
    });
  });

  test.describe("Quick Actions", () => {
    test("Dashboard has quick action links", async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("networkidle");

      await expect(page.getByRole("button", { name: /import papers/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /search library/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /manage projects/i })).toBeVisible();
    });

    test("Quick action navigates to Papers page", async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("networkidle");
      await page.getByRole("button", { name: /import papers/i }).click();
      await expect(page).toHaveURL(/\/papers/);
    });

    test("Quick action navigates to Search page", async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("networkidle");
      await page.getByRole("button", { name: /search library/i }).click();
      await expect(page).toHaveURL(/\/search/);
    });

    test("Quick action navigates to Projects page", async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("networkidle");
      await page.getByRole("button", { name: /manage projects/i }).click();
      await expect(page).toHaveURL(/\/projects/);
    });
  });
});
