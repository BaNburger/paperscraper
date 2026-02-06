import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a transfer conversation via the dialog UI. */
async function createConversation(page: Page, title?: string): Promise<string> {
  const convTitle = title ?? `Conversation ${Date.now()}`;
  await page.getByRole("button", { name: /new conversation/i }).click();
  await page.getByLabel(/title/i).fill(convTitle);
  await page.getByRole("dialog").getByRole("button", { name: /create/i }).click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  return convTitle;
}

test.describe("Transfer Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/transfer");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /technology transfer/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/manage transfer conversations/i)).toBeVisible();
    });

    test("displays New Conversation button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /new conversation/i })).toBeVisible();
    });
  });

  test.describe("Filters", () => {
    test("displays search input", async ({ page }) => {
      await expect(page.getByPlaceholder(/search conversations/i)).toBeVisible();
    });

    test("displays stage filter", async ({ page }) => {
      await expect(page.getByRole("combobox")).toBeVisible();
    });

    test("can filter by stage", async ({ page }) => {
      await page.getByRole("combobox").click();
      await expect(page.getByRole("option", { name: /all stages/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /initial contact/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /discovery/i })).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no conversations", async ({ page }) => {
      await expect(page.getByText(/no conversations yet/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(page.getByText(/start a technology transfer conversation/i)).toBeVisible();
    });

    test("shows New Conversation button in empty state", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /new conversation/i })
      ).toHaveCount(2); // Header + empty state
    });
  });

  test.describe("Create Conversation Dialog", () => {
    test("opens create dialog when clicking New Conversation", async ({ page }) => {
      await page.getByRole("button", { name: /new conversation/i }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/new conversation/i).first()).toBeVisible();
    });

    test("dialog has title field", async ({ page }) => {
      await page.getByRole("button", { name: /new conversation/i }).first().click();
      await expect(page.getByLabel(/title/i)).toBeVisible();
    });

    test("dialog has transfer type selector", async ({ page }) => {
      await page.getByRole("button", { name: /new conversation/i }).first().click();
      await expect(page.getByLabel(/transfer type/i)).toBeVisible();
    });

    test("can select different transfer types", async ({ page }) => {
      await page.getByRole("button", { name: /new conversation/i }).first().click();
      await page.getByLabel(/transfer type/i).click();

      await expect(page.getByRole("option", { name: /patent/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /licensing/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /startup/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /partnership/i })).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /new conversation/i }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("can create a new conversation", async ({ page }) => {
      const convTitle = `Test Conversation ${Date.now()}`;
      await page.getByRole("button", { name: /new conversation/i }).first().click();
      await page.getByLabel(/title/i).fill(convTitle);

      await page.getByRole("dialog").getByRole("button", { name: /create/i }).click();

      await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
      await expect(page.getByText(convTitle).first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Conversation Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createConversation(page);
      await page.waitForTimeout(500);
    });

    test("displays conversation cards after creation", async ({ page }) => {
      await expect(page.locator('a[href*="/transfer/"]').first()).toBeVisible();
    });

    test("shows stage badge on card", async ({ page }) => {
      await expect(page.getByText(/initial contact|discovery|evaluation/i).first()).toBeVisible();
    });

    test("shows type badge on card", async ({ page }) => {
      await expect(page.getByText(/patent|licensing|startup|partnership|other/i).first()).toBeVisible();
    });

    test("shows message count", async ({ page }) => {
      // Look for the message icon count
      await expect(page.locator('svg[class*="MessageSquare"]').first()).toBeVisible();
    });

    test("can click conversation to view details", async ({ page }) => {
      await page.locator('a[href*="/transfer/"]').first().click();
      await expect(page).toHaveURL(/\/transfer\/[^/]+$/);
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /technology transfer/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /new conversation/i }).first()).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /technology transfer/i })).toBeVisible();
    });
  });
});
