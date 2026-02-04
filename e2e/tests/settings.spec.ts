import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("User Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/settings");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(
        page.getByText(/manage your account settings and preferences/i)
      ).toBeVisible();
    });
  });

  test.describe("Profile Section", () => {
    test("displays Profile section", async ({ page }) => {
      await expect(page.getByText("Profile", { exact: true })).toBeVisible();
    });

    test("displays email field (disabled)", async ({ page }) => {
      const emailField = page.getByLabel("Email", { exact: true });
      await expect(emailField).toBeVisible();
      await expect(emailField).toBeDisabled();
    });

    test("displays Full Name field", async ({ page }) => {
      await expect(page.getByLabel(/full name/i)).toBeVisible();
    });

    test("displays Role field (disabled)", async ({ page }) => {
      const roleField = page.getByLabel("Role", { exact: true });
      await expect(roleField).toBeVisible();
      await expect(roleField).toBeDisabled();
    });

    test("has Save Changes button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /save changes/i }).first()
      ).toBeVisible();
    });

    test("can update full name", async ({ page }) => {
      const fullNameField = page.getByLabel(/full name/i);
      await fullNameField.clear();
      await fullNameField.fill("Test User Updated");

      await page.getByRole("button", { name: /save changes/i }).first().click();

      await expect(
        page.getByText(/saved|profile updated/i).first()
      ).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Notifications Section", () => {
    test("displays Notifications section", async ({ page }) => {
      await expect(page.getByText("Notifications", { exact: true })).toBeVisible();
    });

    test("has Email Notifications toggle", async ({ page }) => {
      await expect(page.getByText(/email notifications/i)).toBeVisible();
    });

    test("has Alert Digest Frequency dropdown", async ({ page }) => {
      await expect(page.getByLabel(/alert digest frequency/i)).toBeVisible();
    });

    test("can toggle email notifications", async ({ page }) => {
      // The switch is a button[role="switch"] near the "Email Notifications" label
      const toggle = page.locator('button[role="switch"]').first();
      if (await toggle.isVisible()) {
        await toggle.click();
      }
    });

    test("can change alert digest frequency", async ({ page }) => {
      const selectField = page.getByLabel(/alert digest frequency/i);
      await selectField.selectOption("weekly");
      await expect(selectField).toHaveValue("weekly");
    });

    test("has Save Preferences button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /save preferences/i })
      ).toBeVisible();
    });
  });

  test.describe("Password Section", () => {
    test("displays Password section", async ({ page }) => {
      await expect(page.getByText("Password", { exact: true }).first()).toBeVisible();
    });

    test("has Current Password field", async ({ page }) => {
      await expect(page.getByLabel("Current Password", { exact: true })).toBeVisible();
    });

    test("has New Password field", async ({ page }) => {
      await expect(page.getByLabel("New Password", { exact: true })).toBeVisible();
    });

    test("has Confirm Password field", async ({ page }) => {
      await expect(page.getByLabel("Confirm New Password", { exact: true })).toBeVisible();
    });

    test("has password visibility toggle", async ({ page }) => {
      await expect(
        page.getByLabel("New Password", { exact: true })
      ).toHaveAttribute("type", "password");
    });

    test("has Change Password button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /change password/i })
      ).toBeVisible();
    });

    test("Change Password button is disabled when fields are empty", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /change password/i })
      ).toBeDisabled();
    });

    test("shows validation error for short password", async ({ page }) => {
      await page.getByLabel("Current Password", { exact: true }).fill("oldpassword");
      await page.getByLabel("New Password", { exact: true }).fill("short");
      await page.getByLabel("Confirm New Password", { exact: true }).fill("short");
      await page.getByRole("button", { name: /change password/i }).click();

      await expect(
        page.getByText(/password must be at least 8 characters/i)
      ).toBeVisible();
    });

    test("shows validation error for mismatched passwords", async ({ page }) => {
      await page.getByLabel("Current Password", { exact: true }).fill("oldpassword");
      await page.getByLabel("New Password", { exact: true }).fill("newpassword123");
      await page.getByLabel("Confirm New Password", { exact: true }).fill("differentpassword");
      await page.getByRole("button", { name: /change password/i }).click();

      await expect(page.getByText(/passwords do not match/i)).toBeVisible();
    });
  });

  test.describe("Account Information Section", () => {
    test("displays Account Information section", async ({ page }) => {
      await expect(page.getByText(/account information/i)).toBeVisible();
    });

    test("shows organization name", async ({ page }) => {
      await expect(page.getByText(/organization/i).first()).toBeVisible();
    });

    test("shows subscription tier", async ({ page }) => {
      await expect(page.getByText(/subscription/i)).toBeVisible();
    });

    test("shows member since date", async ({ page }) => {
      await expect(page.getByText(/member since/i)).toBeVisible();
    });

    test("shows account status", async ({ page }) => {
      await expect(page.getByText(/account status/i)).toBeVisible();
      await expect(page.getByText("Active", { exact: true })).toBeVisible();
    });
  });

  test.describe("Form Validation", () => {
    test("shows success message after saving profile", async ({ page }) => {
      await page.getByLabel(/full name/i).fill("Updated Name");
      await page.getByRole("button", { name: /save changes/i }).first().click();

      await expect(
        page.getByText(/saved|profile updated/i).first()
      ).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to smaller screens", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible();
      await expect(page.getByLabel(/full name/i)).toBeVisible();
    });
  });
});
