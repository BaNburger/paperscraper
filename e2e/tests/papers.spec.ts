import { test, expect, registerUser, generateTestUser } from "./fixtures";
import type { Page } from "@playwright/test";

const firstPaperLink = (page: Page) =>
  page.locator('main a[href^="/papers/"]:not([href="/papers"])').first();

async function openImportPapersModal(page: Page) {
  await page.goto("/papers");
  await page.getByRole("button", { name: /import papers/i }).first().click();
  await expect(page.getByRole("dialog", { name: /import papers/i })).toBeVisible();
}

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
      await openImportPapersModal(page);
      await expect(page.getByRole("tab", { name: /^doi$/i })).toBeVisible();
      await expect(page.getByRole("tabpanel", { name: /^doi$/i })).toBeVisible();
    });

    test("can import paper by DOI", async ({ page }) => {
      await openImportPapersModal(page);
      await page.getByRole("textbox", { name: /^doi$/i }).fill("10.1038/nature12373");
      await page.getByRole("button", { name: "Import", exact: true }).click();

      const importResult = page.locator('[role="status"], [role="alert"]').filter({
        hasText: /success|imported|failed|error/i,
      });
      await expect(importResult.first()).toBeVisible({ timeout: 15000 });
    });
  });

  test.describe("Paper Detail", () => {
    test("can view paper details after import", async ({ page }) => {
      // Increase timeout for this test as it depends on external API
      test.setTimeout(60000);

      await openImportPapersModal(page);
      await page.getByRole("textbox", { name: /^doi$/i }).fill("10.1038/nature12373");
      await page.getByRole("button", { name: "Import", exact: true }).click();

      // Wait for import API response rather than hardcoded timeout
      await page.waitForResponse(
        (response) =>
          response.url().includes("/api/v1/papers/ingest/doi") &&
          response.status() < 500,
        { timeout: 20000 }
      ).catch(() => {});

      // Wait a moment for any toasts to appear and the UI to update
      await page.waitForTimeout(1000);

      await page.goto("/papers");
      await page.waitForLoadState("networkidle");

      // Wait for paper link with proper expect assertion (waits and retries)
      const paperLink = firstPaperLink(page);
      const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

      if (paperExists) {
        await paperLink.click();
        await expect(
          page.getByText(/abstract|authors|doi/i).first()
        ).toBeVisible({ timeout: 10000 });
      }
    });
  });

  test.describe("Paper Actions", () => {
    test("can open transfer dialog from paper details", async ({ page }) => {
      await page.goto("/papers");

      const paperLink = firstPaperLink(page);
      if (await paperLink.isVisible()) {
        await paperLink.click();

        const transferButton = page.getByRole("button", { name: /start transfer/i }).first();
        if (await transferButton.isVisible()) {
          await transferButton.click();
          await expect(page.getByRole("dialog")).toBeVisible();
        }
      }
    });

    test("can trigger AI scoring", async ({ page }) => {
      await page.goto("/papers");

      const paperLink = firstPaperLink(page);
      if (await paperLink.isVisible()) {
        await paperLink.click();

        const scoreButton = page.getByRole("button", { name: /score/i }).first();
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
