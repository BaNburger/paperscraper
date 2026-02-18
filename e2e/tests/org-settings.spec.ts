import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Organization Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/settings/organization");
    await expect(
      page.getByRole("heading", { level: 1, name: /organization settings/i })
    ).toBeVisible();
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(
        page.getByRole("heading", { level: 1, name: /organization settings/i })
      ).toBeVisible();
    });

    test("displays organization info section", async ({ page }) => {
      await expect(page.getByRole("heading", { name: /organization profile/i })).toBeVisible();
    });
  });

  test.describe("Organization Info", () => {
    test("shows organization name", async ({ page }) => {
      const nameField = page.getByLabel(/organization name/i);
      await expect(nameField).toBeVisible();
      await expect(nameField).not.toHaveValue("");
    });

    test("shows organization type", async ({ page }) => {
      await expect(page.getByLabel(/organization type/i)).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(
        page.getByRole("heading", { level: 1, name: /organization settings/i })
      ).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(
        page.getByRole("heading", { level: 1, name: /organization settings/i })
      ).toBeVisible();
    });
  });
});
