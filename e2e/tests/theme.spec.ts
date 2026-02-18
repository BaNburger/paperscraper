import { test, expect, registerUser, generateTestUser } from "./fixtures";

const THEME_TOGGLE_LABEL = /toggle theme|design umschalten/i;
const THEME_DARK_LABEL = /dark|dunkel/i;
const THEME_LIGHT_LABEL = /light|hell/i;

function themeToggle(page: Parameters<typeof test>[0]["page"]) {
  return page.getByRole("button", { name: THEME_TOGGLE_LABEL }).first();
}

async function openThemeMenu(page: Parameters<typeof test>[0]["page"]) {
  await themeToggle(page).click();
  await expect(page.getByRole("menuitem", { name: THEME_LIGHT_LABEL })).toBeVisible();
}

async function selectTheme(
  page: Parameters<typeof test>[0]["page"],
  themeName: RegExp
) {
  await openThemeMenu(page);
  await page.getByRole("menuitem", { name: themeName }).click();
}

test.describe("Theme Switching", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
  });

  test.describe("Theme Toggle", () => {
    test("can access theme toggle in navbar", async ({ page }) => {
      await expect(themeToggle(page)).toBeVisible();
    });

    test("can toggle to dark mode", async ({ page }) => {
      await selectTheme(page, THEME_DARK_LABEL);
      await expect(page.locator("html")).toHaveClass(/\bdark\b/);
    });

    test("dark mode persists across navigation", async ({ page }) => {
      await selectTheme(page, THEME_DARK_LABEL);
      await expect(page.locator("html")).toHaveClass(/\bdark\b/);

      await page.goto("/papers");
      await page.waitForLoadState("networkidle");

      await expect(page.locator("html")).toHaveClass(/\bdark\b/);
    });

    test("dark mode affects page background", async ({ page }) => {
      await selectTheme(page, THEME_LIGHT_LABEL);
      const lightBg = await page.locator("body").evaluate((el) =>
        window.getComputedStyle(el).backgroundColor
      );

      await selectTheme(page, THEME_DARK_LABEL);
      const darkBg = await page.locator("body").evaluate((el) =>
        window.getComputedStyle(el).backgroundColor
      );

      expect(lightBg).not.toBe(darkBg);
    });
  });

  test.describe("Dark Mode Visual Consistency", () => {
    test.beforeEach(async ({ page }) => {
      await selectTheme(page, THEME_DARK_LABEL);
      await expect(page.locator("html")).toHaveClass(/\bdark\b/);
    });

    test("dashboard is readable in dark mode", async ({ page }) => {
      await expect(page.getByText(/welcome back/i)).toBeVisible();
      await expect(page.getByText(/total papers/i)).toBeVisible();
    });

    test("papers page is readable in dark mode", async ({ page }) => {
      await page.goto("/papers");
      await expect(page.getByRole("heading", { level: 1, name: /papers/i })).toBeVisible();
    });

    test("search page is readable in dark mode", async ({ page }) => {
      await page.goto("/search");
      await expect(page.getByRole("heading", { level: 1, name: /search/i })).toBeVisible();
    });

    test("settings page is readable in dark mode", async ({ page }) => {
      await page.goto("/settings");
      await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible();
    });
  });

  test.describe("Light Mode Visual Consistency", () => {
    test("dashboard is readable in light mode", async ({ page }) => {
      await expect(page.getByText(/welcome back/i)).toBeVisible();
      await expect(page.getByText(/total papers/i)).toBeVisible();
    });

    test("papers page is readable in light mode", async ({ page }) => {
      await page.goto("/papers");
      await expect(page.getByRole("heading", { level: 1, name: /papers/i })).toBeVisible();
    });
  });

  test.describe("Theme on Different Viewports", () => {
    test("theme toggle works on tablet", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(themeToggle(page)).toBeVisible();
      await selectTheme(page, THEME_DARK_LABEL);
      await expect(page.locator("html")).toHaveClass(/\bdark\b/);
    });

    test("theme toggle works on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(themeToggle(page)).toBeVisible();
      await selectTheme(page, THEME_DARK_LABEL);
      await expect(page.locator("html")).toHaveClass(/\bdark\b/);
    });
  });
});
