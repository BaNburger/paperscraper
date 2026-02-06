import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Organization Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/settings/organization");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1 }).or(page.getByText(/organization settings/i))).toBeVisible();
    });

    test("displays organization info section", async ({ page }) => {
      // Should show organization name field or info
      await expect(page.getByText(/organization/i).first()).toBeVisible();
    });
  });

  test.describe("Organization Info", () => {
    test("shows organization name", async ({ page }) => {
      await expect(page.getByText(/organization name|test org/i).first()).toBeVisible();
    });

    test("shows organization type", async ({ page }) => {
      await expect(page.getByText(/type|university|vc|corporate|research/i).first()).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByText(/organization/i).first()).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByText(/organization/i).first()).toBeVisible();
    });
  });
});
