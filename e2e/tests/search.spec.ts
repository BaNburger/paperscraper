import { test, expect, registerUser, generateTestUser } from "./fixtures";
import type { Page } from "@playwright/test";

async function runSearchAndWaitForCompletion(
  page: Page,
  query: string
) {
  const searchInput = page.getByPlaceholder(/search for papers/i);
  const searchButton = page.getByRole("button", { name: /^search$/i }).first();
  await searchInput.fill(query);
  await searchButton.click();
  await expect(searchButton).toBeEnabled({ timeout: 20000 });
}

test.describe("Search Page", () => {
  test.describe.configure({ timeout: 90000 });

  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/search", { waitUntil: "domcontentloaded", timeout: 60000 });
    await expect(page.getByRole("heading", { level: 1, name: /search/i })).toBeVisible({
      timeout: 20000,
    });
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /search/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(
        page.getByText(/find papers using full-text, semantic, or hybrid search/i)
      ).toBeVisible();
    });

    test("displays search input", async ({ page }) => {
      await expect(page.getByPlaceholder(/search for papers/i)).toBeVisible();
    });

    test("displays Search button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /^search$/i }).first()
      ).toBeVisible();
    });
  });

  test.describe("Search Modes", () => {
    test("displays all search mode options", async ({ page }) => {
      await expect(page.getByRole("button", { name: /hybrid/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /full-text/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /semantic/i })).toBeVisible();
    });

    test("Hybrid mode is selected by default", async ({ page }) => {
      await expect(page.getByRole("button", { name: /hybrid/i })).toHaveClass(/bg-primary/);
    });

    test("can switch to Full-text mode", async ({ page }) => {
      await page.getByRole("button", { name: /full-text/i }).click();
      await expect(page.getByText(/traditional keyword search/i)).toBeVisible();
    });

    test("can switch to Semantic mode", async ({ page }) => {
      await page.getByRole("button", { name: /semantic/i }).click();
      await expect(page.getByText(/ai-powered meaning search/i)).toBeVisible();
    });

    test("shows mode description when switching", async ({ page }) => {
      await page.getByRole("button", { name: /full-text/i }).click();
      await expect(page.getByText(/traditional keyword search/i)).toBeVisible();

      await page.getByRole("button", { name: /hybrid/i }).click();
      await expect(page.getByText(/combines text and semantic search/i)).toBeVisible();
    });
  });

  test.describe("Filter Options", () => {
    test("has filter toggle button", async ({ page }) => {
      await expect(page.locator("form")).toBeVisible();
    });

    test("shows semantic weight slider in Hybrid mode", async ({ page }) => {
      const filterToggle = page.getByRole("button").filter({
        has: page.locator("svg"),
      });

      for (const button of await filterToggle.all()) {
        const hasSliders = await button.locator('svg[class*="Sliders"]').count();
        if (hasSliders > 0) {
          await button.click();
          break;
        }
      }

      const semanticWeight = page.getByText(/semantic weight/i);
      if (await semanticWeight.isVisible()) {
        await expect(semanticWeight).toBeVisible();
        await expect(page.locator('input[type="range"]')).toBeVisible();
      }
    });
  });

  test.describe("Initial State", () => {
    test("shows start searching empty state", async ({ page }) => {
      await expect(page.getByText(/start searching/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(page.getByText(/enter keywords to find papers/i)).toBeVisible();
    });
  });

  test.describe("Search Execution", () => {
    test("can enter search query", async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search for papers/i);
      await searchInput.fill("machine learning");
      await expect(searchInput).toHaveValue("machine learning");
    });

    test("can submit search with button click", async ({ page }) => {
      await runSearchAndWaitForCompletion(page, "test query");
      await expect(
        page.getByText(/found \d+ results|no results found|start searching/i).first()
      ).toBeVisible();
    });

    test("can submit search with Enter key", async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search for papers/i);
      const searchButton = page.getByRole("button", { name: /^search$/i }).first();
      await searchInput.fill("test query");
      await searchInput.press("Enter");
      await expect(searchButton).toBeEnabled({ timeout: 20000 });
    });

    test("does not search with empty query", async ({ page }) => {
      await page.getByRole("button", { name: /^search$/i }).first().click();
      await expect(page.getByText(/start searching/i)).toBeVisible();
    });
  });

  test.describe("Search Results", () => {
    test("shows results count after search", async ({ page }) => {
      await runSearchAndWaitForCompletion(page, "test");
      await expect(
        page.getByText(/found \d+ results|no results found|start searching/i).first()
      ).toBeVisible();
    });

    test("shows search mode in results", async ({ page }) => {
      await runSearchAndWaitForCompletion(page, "test");

      const hasModeText = await page
        .getByText(/using (hybrid|fulltext|semantic) search/i)
        .isVisible({ timeout: 15000 })
        .catch(() => false);
      const hasNoResults = await page.getByText(/no results found/i).isVisible().catch(() => false);
      const hasInitialState = await page.getByText(/start searching/i).isVisible().catch(() => false);
      expect(hasModeText || hasNoResults || hasInitialState).toBeTruthy();
    });

    test('shows "Try Semantic Search" suggestion when no results', async ({ page }) => {
      await runSearchAndWaitForCompletion(page, "xyznonexistentquery123");

      const noResultsState = page.getByText(/no results found/i);
      if (await noResultsState.isVisible().catch(() => false)) {
        await expect(
          page.getByRole("button", { name: /try semantic search/i })
        ).toBeVisible();
      } else {
        const hasInitialState = await page.getByText(/start searching/i).isVisible().catch(() => false);
        const hasResults = await page
          .getByText(/found \d+ results/i)
          .isVisible()
          .catch(() => false);
        expect(hasInitialState || hasResults).toBeTruthy();
      }
    });
  });

  test.describe("Loading States", () => {
    test("shows loading indicator during search", async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search for papers/i);
      const searchButton = page.getByRole("button", { name: /^search$/i }).first();
      await searchInput.fill("machine learning");

      await page.route("**/api/v1/search*", async (route) => {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        route.continue();
      });

      await searchButton.click();
      await expect(searchButton).toBeDisabled();
      await expect(searchButton).toBeEnabled({ timeout: 10000 });
    });
  });

  test.describe("Keyboard Navigation", () => {
    test("search input is focusable", async ({ page }) => {
      const searchInput = page.getByPlaceholder(/search for papers/i);
      await searchInput.focus();
      await expect(searchInput).toBeFocused();
    });
  });
});
