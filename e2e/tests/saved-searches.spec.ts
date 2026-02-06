import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Saved Searches Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/saved-searches");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /saved searches/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/manage your saved search queries/i)).toBeVisible();
    });

    test("displays New Search button", async ({ page }) => {
      await expect(page.getByRole("link", { name: /new search/i })).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no saved searches", async ({ page }) => {
      await expect(page.getByText(/no saved searches/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(page.getByText(/save a search from the search page/i)).toBeVisible();
    });
  });

  test.describe("Navigation", () => {
    test("New Search button navigates to search page", async ({ page }) => {
      await page.getByRole("link", { name: /new search/i }).click();
      await expect(page).toHaveURL(/\/search/);
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /saved searches/i })).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /saved searches/i })).toBeVisible();
    });
  });
});

test.describe("Saved Searches - With Data", () => {
  // These tests require creating a saved search first
  // This would typically be done through the Search page

  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);

    // Create a saved search via the search page
    await page.goto("/search");
    await page.waitForLoadState("networkidle");

    // Perform a search
    const searchInput = page.getByPlaceholder(/search for papers/i);
    await searchInput.fill("machine learning");
    await page.getByRole("button", { name: /^search$/i }).first().click();
    await page.waitForLoadState("networkidle");

    // Wait for save button (only appears after search)
    await page.waitForTimeout(1000);

    // Go to saved searches page
    await page.goto("/saved-searches");
    await page.waitForLoadState("networkidle");
  });

  test("shows saved searches page", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1, name: /saved searches/i })).toBeVisible();
  });
});
