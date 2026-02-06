import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a group via the dialog UI. Returns the group name. */
async function createGroup(page: Page, name?: string): Promise<string> {
  const groupName = name ?? `Group ${Date.now()}`;
  await page.getByRole("button", { name: /new group/i }).click();
  await page.getByLabel(/group name/i).fill(groupName);
  await page.getByRole("dialog").getByRole("button", { name: /create group/i }).click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  return groupName;
}

test.describe("Groups Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/groups");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /researcher groups/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/organize researchers into groups/i)).toBeVisible();
    });

    test("displays New Group button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /new group/i })).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no groups", async ({ page }) => {
      await expect(page.getByText(/no groups yet/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(page.getByText(/create a group to organize researchers/i)).toBeVisible();
    });

    test("shows Create Group button in empty state", async ({ page }) => {
      await expect(page.getByRole("button", { name: /create group/i })).toBeVisible();
    });
  });

  test.describe("Create Group Dialog", () => {
    test("opens create dialog when clicking New Group", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/create group/i).first()).toBeVisible();
    });

    test("dialog has group name field", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();
      await expect(page.getByLabel(/group name/i)).toBeVisible();
    });

    test("dialog has description field", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();
      await expect(page.getByLabel(/description/i)).toBeVisible();
    });

    test("dialog has type selector", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();
      await expect(page.getByLabel(/type/i)).toBeVisible();
    });

    test("dialog has keywords field", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();
      await expect(page.getByLabel(/keywords/i)).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("can create a new group", async ({ page }) => {
      const groupName = `Test Group ${Date.now()}`;
      await page.getByRole("button", { name: /new group/i }).click();
      await page.getByLabel(/group name/i).fill(groupName);
      await page.getByLabel(/description/i).fill("Test description");

      await page.getByRole("dialog").getByRole("button", { name: /create group/i }).click();

      await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
      await expect(page.getByText(groupName).first()).toBeVisible({ timeout: 5000 });
    });

    test("can select different group types", async ({ page }) => {
      await page.getByRole("button", { name: /new group/i }).click();

      // Open the type selector
      await page.getByLabel(/type/i).click();

      // Check all options are available
      await expect(page.getByRole("option", { name: /custom/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /mailing list/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /speaker pool/i })).toBeVisible();
    });
  });

  test.describe("Group Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createGroup(page);
      await page.waitForTimeout(500);
    });

    test("displays group cards after creation", async ({ page }) => {
      await expect(page.locator(".cursor-pointer").first()).toBeVisible();
    });

    test("shows member count", async ({ page }) => {
      await expect(page.getByText(/\d+ members/i).first()).toBeVisible();
    });

    test("shows group type badge", async ({ page }) => {
      await expect(page.getByText(/custom|mailing list|speaker pool/i).first()).toBeVisible();
    });

    test("can click group to view details", async ({ page }) => {
      await page.locator(".cursor-pointer").first().click();
      // Should show detail panel
      await expect(page.getByText(/members/i).first()).toBeVisible();
    });
  });

  test.describe("Group Detail Panel", () => {
    test("shows 'Select a group' message when no group selected", async ({ page }) => {
      await expect(page.getByText(/select a group to view details/i)).toBeVisible();
    });

    test("shows group details when selected", async ({ page }) => {
      await createGroup(page, `Detail Test ${Date.now()}`);
      await page.waitForTimeout(500);

      // Click the group card
      await page.locator(".cursor-pointer").first().click();

      // Should show members section
      await expect(page.getByText(/members/i).first()).toBeVisible();
    });

    test("shows Export CSV button when group is selected", async ({ page }) => {
      await createGroup(page);
      await page.waitForTimeout(500);
      await page.locator(".cursor-pointer").first().click();

      await expect(page.getByRole("button", { name: /export csv/i })).toBeVisible();
    });
  });

  test.describe("Delete Group", () => {
    test("shows delete confirmation dialog", async ({ page }) => {
      await createGroup(page, `Delete Test ${Date.now()}`);
      await page.waitForTimeout(500);

      // Click the group card to select it
      await page.locator(".cursor-pointer").first().click();

      // Find and click delete button
      await page.getByRole("button").filter({ has: page.locator('svg[class*="Trash"]') }).click();

      // Check confirmation dialog
      await expect(page.getByText(/are you sure/i)).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /researcher groups/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /new group/i })).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /researcher groups/i })).toBeVisible();
    });
  });
});
