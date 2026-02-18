import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a knowledge source via the dialog UI. */
async function createKnowledgeSource(page: Page, title?: string): Promise<string> {
  const ksTitle = title ?? `Knowledge Source ${Date.now()}`;
  await page.getByRole("button", { name: /add source/i }).first().click();
  await page.getByLabel(/title/i).fill(ksTitle);
  await page.locator('textarea[id="ksContent"]').fill("Test content for this knowledge source.");

  const createResponsePromise = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/v1\/knowledge\/(personal|organization)/.test(response.url()),
    { timeout: 20000 }
  );

  await page.getByRole("dialog").getByRole("button", { name: /create/i }).click();

  const createResponse = await createResponsePromise;
  expect(createResponse.status()).toBeGreaterThanOrEqual(200);
  expect(createResponse.status()).toBeLessThan(400);

  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 15000 });
  await expect(page.getByRole("heading", { level: 3, name: ksTitle })).toBeVisible({
    timeout: 20000,
  });
  return ksTitle;
}

test.describe("Knowledge Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/knowledge", { waitUntil: "domcontentloaded", timeout: 60000 });
    await expect(page.getByRole("heading", { level: 1, name: /knowledge base/i })).toBeVisible({
      timeout: 20000,
    });
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /knowledge base/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/manage knowledge sources for ai-powered analysis/i)).toBeVisible();
    });

    test("displays Add Source button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /add source/i }).first()).toBeVisible();
    });
  });

  test.describe("Tabs", () => {
    test("displays Personal tab", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /personal|pers.?nlich/i }).first()
      ).toBeVisible();
    });

    test("Personal tab is active by default", async ({ page }) => {
      await expect(
        page.getByText(/no personal sources yet|noch keine .*quellen/i).first()
      ).toBeVisible();
    });

    test("Organization tab visible for admin", async ({ page }) => {
      // New users are admins of their org
      await expect(
        page.getByRole("button", { name: /organization|organisation/i }).first()
      ).toBeVisible();
    });

    test("can switch to Organization tab", async ({ page }) => {
      await page.getByRole("button", { name: /organization|organisation/i }).first().click();
      await expect(
        page.getByText(/no organization sources yet|noch keine .*quellen/i).first()
      ).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no knowledge sources", async ({ page }) => {
      await expect(page.getByText(/no personal sources yet/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(page.getByText(/enhance ai analysis with domain-specific context/i)).toBeVisible();
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
      await expect(page.getByText(/add source/i).first()).toBeVisible();
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
      await createKnowledgeSource(page, ksTitle);
      await expect(page.getByRole("heading", { level: 3, name: ksTitle })).toBeVisible();
    });
  });

  test.describe("Knowledge Source Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createKnowledgeSource(page);
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
      await expect(
        page.locator('svg.lucide-pencil, svg[data-lucide="pencil"], svg[class*="pencil"]').first()
      ).toBeVisible();
    });

    test("shows delete button on hover", async ({ page }) => {
      const card = page.locator(".group.relative").first();
      await card.hover();
      await expect(
        page.locator('svg.lucide-trash2, svg[data-lucide="trash2"], svg[class*="trash"]').first()
      ).toBeVisible();
    });
  });

  test.describe("Delete Confirmation", () => {
    test("shows delete confirmation dialog", async ({ page }) => {
      await createKnowledgeSource(page, `Delete Test ${Date.now()}`);

      const card = page.locator(".group.relative").first();
      await card.hover();
      await page
        .getByRole("button")
        .filter({
          has: page.locator('svg.lucide-trash2, svg[data-lucide="trash2"], svg[class*="trash"]'),
        })
        .first()
        .click();

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
