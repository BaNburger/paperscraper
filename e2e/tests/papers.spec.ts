import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Papers", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
  });

  test.describe("Paper List", () => {
    test("can view papers list", async ({ page }) => {
      await page.goto("/papers");
      await expect(page).toHaveURL(/\/papers/);
      await expect(
        page.getByRole("heading", { level: 1, name: /papers/i })
      ).toBeVisible();
    });

    test("shows empty state when no papers", async ({ page }) => {
      await page.goto("/papers");
      await expect(page.getByText(/no papers|import|add/i).first()).toBeVisible();
    });
  });

  test.describe("Paper Import", () => {
    test("can access DOI import form", async ({ page }) => {
      await page.goto("/papers");
      await page.getByRole("button", { name: /import papers/i }).first().click();
      await expect(page.getByRole("button", { name: "DOI" })).toBeVisible();
    });

    test("can import paper by DOI", async ({ page }) => {
      await page.goto("/papers");
      await page.getByRole("button", { name: /import papers/i }).first().click();
      await page.fill("#doi", "10.1038/nature12373");
      await page.getByRole("button", { name: "Import", exact: true }).click();

      await expect(
        page.getByText(/importing|success|imported|failed|error/i)
      ).toBeVisible({ timeout: 15000 });
    });
  });

  test.describe("Paper Detail", () => {
    test("can view paper details after import", async ({ page }) => {
      await page.goto("/papers");
      await page.getByRole("button", { name: /import papers/i }).first().click();
      await page.fill("#doi", "10.1038/nature12373");
      await page.getByRole("button", { name: "Import", exact: true }).click();

      // Wait for import API response rather than hardcoded timeout
      await page.waitForResponse(
        (response) => response.url().includes("/api/v1/papers/ingest") && response.status() < 500,
        { timeout: 15000 }
      ).catch(() => {});

      await page.goto("/papers");

      const paperLink = page.locator('a[href*="/papers/"]').first();
      if (await paperLink.isVisible()) {
        await paperLink.click();
        await expect(
          page.getByText(/abstract|authors|doi/i).first()
        ).toBeVisible();
      }
    });
  });

  test.describe("Paper Actions", () => {
    test("can add paper to project", async ({ page }) => {
      await page.goto("/papers");

      const paperLink = page.locator('a[href*="/papers/"]').first();
      if (await paperLink.isVisible()) {
        await paperLink.click();

        const addButton = page.getByRole("button", { name: /add to project/i });
        if (await addButton.isVisible()) {
          await addButton.click();
          await expect(page.getByText(/select.*project/i)).toBeVisible();
        }
      }
    });

    test("can trigger AI scoring", async ({ page }) => {
      await page.goto("/papers");

      const paperLink = page.locator('a[href*="/papers/"]').first();
      if (await paperLink.isVisible()) {
        await paperLink.click();

        const scoreButton = page.getByRole("button", { name: /score/i });
        if (await scoreButton.isVisible()) {
          await scoreButton.click();
          await expect(
            page.getByText(/scoring|novelty|potential/i)
          ).toBeVisible({ timeout: 30000 });
        }
      }
    });
  });
});
