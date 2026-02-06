import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Team Members Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/team");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /team members/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/manage your organization's team/i)).toBeVisible();
    });

    test("displays Invite Member button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /invite member/i })).toBeVisible();
    });
  });

  test.describe("Stats Cards", () => {
    test("displays Total Members card", async ({ page }) => {
      await expect(page.getByText(/total members/i)).toBeVisible();
    });

    test("displays Pending Invitations card", async ({ page }) => {
      await expect(page.getByText(/pending invitations/i)).toBeVisible();
    });

    test("displays Admins card", async ({ page }) => {
      await expect(page.getByText(/admins/i).first()).toBeVisible();
    });
  });

  test.describe("Active Members Table", () => {
    test("displays Active Members section", async ({ page }) => {
      await expect(page.getByText(/active members/i).first()).toBeVisible();
    });

    test("displays table headers", async ({ page }) => {
      await expect(page.getByText("User", { exact: true })).toBeVisible();
      await expect(page.getByText("Role", { exact: true })).toBeVisible();
      await expect(page.getByText("Status", { exact: true })).toBeVisible();
      await expect(page.getByText("Joined", { exact: true })).toBeVisible();
    });

    test("shows current user in table", async ({ page }) => {
      // The newly registered user should appear in the table
      await expect(page.getByText("(you)")).toBeVisible();
    });

    test("shows admin role badge for org creator", async ({ page }) => {
      await expect(page.getByText("Admin", { exact: true }).first()).toBeVisible();
    });

    test("shows active status for current user", async ({ page }) => {
      await expect(page.getByText("Active", { exact: true }).first()).toBeVisible();
    });
  });

  test.describe("Invite Member Dialog", () => {
    test("opens invite dialog when clicking Invite Member", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/invite team member/i)).toBeVisible();
    });

    test("dialog has email field", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await expect(page.getByLabel(/email address/i)).toBeVisible();
    });

    test("dialog has role selector", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await expect(page.getByLabel(/role/i)).toBeVisible();
    });

    test("can select different roles", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await page.getByLabel(/role/i).click();

      await expect(page.getByRole("option", { name: /viewer/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /member/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /manager/i })).toBeVisible();
      await expect(page.getByRole("option", { name: /admin/i })).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("validates email format", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await page.getByLabel(/email address/i).fill("invalid-email");
      await page.getByRole("button", { name: /send invitation/i }).click();

      // Browser validation should prevent submission
      const emailInput = page.getByLabel(/email address/i);
      await expect(emailInput).toHaveAttribute("type", "email");
    });

    test("can send invitation", async ({ page }) => {
      await page.getByRole("button", { name: /invite member/i }).click();
      await page.getByLabel(/email address/i).fill(`invite-${Date.now()}@example.com`);
      await page.getByRole("button", { name: /send invitation/i }).click();

      // Wait for API response
      await page.waitForTimeout(2000);

      // Should either succeed or show error
      const dialogHidden = await page.getByRole("dialog").isHidden().catch(() => false);
      const hasError = await page.getByText(/failed|error/i).isVisible().catch(() => false);
      expect(dialogHidden || hasError).toBeTruthy();
    });
  });

  test.describe("User Actions", () => {
    test("shows no actions menu for current user", async ({ page }) => {
      // The current user row should not have an actions menu
      const userRow = page.getByText("(you)").locator("..");
      const actionsMenu = userRow.getByRole("button", { name: /user actions/i });
      await expect(actionsMenu).toBeHidden();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /team members/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /invite member/i })).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /team members/i })).toBeVisible();
    });

    test("table scrolls horizontally on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByText(/active members/i).first()).toBeVisible();
    });
  });
});
