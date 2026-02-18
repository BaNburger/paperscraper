import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a submission via the dialog UI. */
async function createSubmission(page: Page, title?: string): Promise<string> {
  const subTitle = title ?? `Submission ${Date.now()}`;
  await page.getByRole("button", { name: /new submission/i }).first().click();
  await page.getByLabel(/title/i).fill(subTitle);
  await page.getByRole("dialog").getByRole("button", { name: /create draft/i }).click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  await expect(page.getByText(subTitle).first()).toBeVisible({ timeout: 5000 });
  return subTitle;
}

test.describe("Submissions Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/submissions");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /research submissions/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/review and manage research submissions/i)).toBeVisible();
    });

    test("displays New Submission button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /new submission/i }).first()).toBeVisible();
    });
  });

  test.describe("Filters", () => {
    test("displays status filter", async ({ page }) => {
      await expect(page.getByRole("combobox")).toBeVisible();
    });

    test("can filter by status", async ({ page }) => {
      await page.getByRole("combobox").click();
      await expect(page.getByRole("option", { name: /all statuses/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /draft/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /submitted/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /approved/i })).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no submissions", async ({ page }) => {
      await expect(page.getByText(/no submissions yet/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(
        page.getByText(/submit your first research to get started|create a submission to start/i)
      ).toBeVisible();
    });

    test("shows New Submission button in empty state", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /new submission/i })
      ).toHaveCount(2); // Header + empty state
    });
  });

  test.describe("Create Submission Dialog", () => {
    test("opens create dialog when clicking New Submission", async ({ page }) => {
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/new submission/i).first()).toBeVisible();
    });

    test("dialog has title field", async ({ page }) => {
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await expect(page.getByLabel(/title/i)).toBeVisible();
    });

    test("dialog has abstract field", async ({ page }) => {
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await expect(page.getByLabel(/abstract/i)).toBeVisible();
    });

    test("dialog has research field", async ({ page }) => {
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await expect(page.getByLabel(/research field/i)).toBeVisible();
    });

    test("dialog has keywords field", async ({ page }) => {
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await expect(page.getByLabel(/keywords/i)).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("can create a new submission", async ({ page }) => {
      const subTitle = `Test Submission ${Date.now()}`;
      await page.getByRole("button", { name: /new submission/i }).first().click();
      await page.getByLabel(/title/i).fill(subTitle);

      await page.getByRole("dialog").getByRole("button", { name: /create draft/i }).click();

      await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
      await expect(page.getByText(subTitle).first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Submission Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createSubmission(page);
      await page.waitForTimeout(500);
    });

    test("displays submission cards after creation", async ({ page }) => {
      await expect(page.locator(".cursor-pointer").first()).toBeVisible();
    });

    test("shows status badge on card", async ({ page }) => {
      await expect(page.getByText(/draft|submitted|under review|approved|rejected/i).first()).toBeVisible();
    });

    test("can click submission to view details", async ({ page }) => {
      await page.locator(".cursor-pointer").first().click();
      // Should show detail panel
      await expect(page.getByRole("button", { name: /submit for review/i })).toBeVisible();
    });
  });

  test.describe("Submission Detail Panel", () => {
    test("shows 'Select a submission' message when no submission selected", async ({ page }) => {
      await expect(page.getByText(/select a submission to view details/i)).toBeVisible();
    });

    test("shows submission details when selected", async ({ page }) => {
      await createSubmission(page, `Detail Test ${Date.now()}`);
      await page.waitForTimeout(500);

      // Click the submission card
      await page.locator(".cursor-pointer").first().click();

      // Should show status and actions
      await expect(page.getByText(/draft/i).first()).toBeVisible();
    });

    test("shows Submit for Review button for draft submissions", async ({ page }) => {
      await createSubmission(page);
      await page.waitForTimeout(500);
      await page.locator(".cursor-pointer").first().click();

      await expect(page.getByRole("button", { name: /submit for review/i })).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /research submissions/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /new submission/i }).first()).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /research submissions/i })).toBeVisible();
    });
  });
});
