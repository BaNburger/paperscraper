import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a knowledge source via the dialog UI. */
async function createKnowledgeSource(page: Page, title?: string): Promise<string> {
  const ksTitle = title ?? `Knowledge Source ${Date.now()}`;
  await page.getByRole("button", { name: /add source/i }).click();
  await page.getByLabel(/title/i).fill(ksTitle);
  await page.locator('textarea[id="ksContent"]').fill("Test content for this knowledge source.");
  await page.getByRole("dialog").getByRole("button", { name: /create/i }).click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  return ksTitle;
}

test.describe("Knowledge Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/knowledge");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /knowledge base/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/manage knowledge sources to personalize/i)).toBeVisible();
    });

    test("displays Add Source button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /add source/i })).toBeVisible();
    });
  });

  test.describe("Tabs", () => {
    test("displays Personal tab", async ({ page }) => {
      await expect(page.getByRole("button", { name: /personal/i })).toBeVisible();
    });

    test("Personal tab is active by default", async ({ page }) => {
      const personalTab = page.getByRole("button", { name: /personal/i });
      await expect(personalTab).toHaveClass(/bg-primary/);
    });

    test("Organization tab visible for admin", async ({ page }) => {
      // New users are admins of their org
      await expect(page.getByRole("button", { name: /organization/i })).toBeVisible();
    });

    test("can switch to Organization tab", async ({ page }) => {
      await page.getByRole("button", { name: /organization/i }).click();
      await expect(page.getByRole("button", { name: /organization/i })).toHaveClass(/bg-primary/);
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no knowledge sources", async ({ page }) => {
      await expect(page.getByText(/no personal knowledge sources/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(page.getByText(/add knowledge sources to help the ai/i)).toBeVisible();
    });

    test("shows Add Source button in empty state", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /add source/i })
      ).toHaveCount(2); // Header + empty state
    });
  });

  test.describe("Create Knowledge Source Dialog", () => {
    test("opens create dialog when clicking Add Source", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/add knowledge source/i).first()).toBeVisible();
    });

    test("dialog has title field", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await expect(page.getByLabel(/title/i)).toBeVisible();
    });

    test("dialog has content field", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await expect(page.getByLabel(/content/i)).toBeVisible();
    });

    test("dialog has type selector", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await expect(page.getByLabel(/type/i)).toBeVisible();
    });

    test("can select different types", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await page.getByLabel(/type/i).click();

      await expect(page.getByRole("option", { name: /research focus/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /industry context/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /custom/i })).toBeVisible();
    });

    test("dialog has tags field", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await expect(page.getByLabel(/tags/i)).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /add source/i }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("can create a new knowledge source", async ({ page }) => {
      const ksTitle = `Test Knowledge ${Date.now()}`;
      await page.getByRole("button", { name: /add source/i }).first().click();
      await page.getByLabel(/title/i).fill(ksTitle);
      await page.locator('textarea[id="ksContent"]').fill("Test content");

      await page.getByRole("dialog").getByRole("button", { name: /create/i }).click();

      await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
      await expect(page.getByText(ksTitle).first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Knowledge Source Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createKnowledgeSource(page);
      await page.waitForTimeout(500);
    });

    test("displays knowledge source cards after creation", async ({ page }) => {
      await expect(page.locator(".group.relative").first()).toBeVisible();
    });

    test("shows type badge on card", async ({ page }) => {
      await expect(page.getByText(/custom|research focus|industry context/i).first()).toBeVisible();
    });

    test("shows content preview", async ({ page }) => {
      await expect(page.getByText(/test content/i).first()).toBeVisible();
    });

    test("shows edit button on hover", async ({ page }) => {
      const card = page.locator(".group.relative").first();
      await card.hover();
      await expect(page.locator('svg[class*="Pencil"]').first()).toBeVisible();
    });

    test("shows delete button on hover", async ({ page }) => {
      const card = page.locator(".group.relative").first();
      await card.hover();
      await expect(page.locator('svg[class*="Trash"]').first()).toBeVisible();
    });
  });

  test.describe("Delete Confirmation", () => {
    test("shows delete confirmation dialog", async ({ page }) => {
      await createKnowledgeSource(page, `Delete Test ${Date.now()}`);
      await page.waitForTimeout(500);

      const card = page.locator(".group.relative").first();
      await card.hover();
      await page.getByRole("button").filter({ has: page.locator('svg[class*="Trash"]') }).first().click();

      await expect(page.getByText(/are you sure/i)).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /knowledge base/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /add source/i }).first()).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /knowledge base/i })).toBeVisible();
    });
  });
});
