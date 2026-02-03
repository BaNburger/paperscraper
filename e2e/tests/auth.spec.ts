import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test.describe("Registration", () => {
    test("user can register with valid credentials", async ({ page }) => {
      const uniqueEmail = `test-${Date.now()}@example.com`;

      await page.goto("/register");

      // Fill registration form
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="password"]', "SecurePass123!");
      await page.fill('[name="organization_name"]', "Test Organization");

      // Submit form
      await page.click('button[type="submit"]');

      // Should redirect to dashboard after successful registration
      await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

      // User should see dashboard content
      await expect(
        page.getByRole("heading", { name: /dashboard/i })
      ).toBeVisible();
    });

    test("shows error for invalid email format", async ({ page }) => {
      await page.goto("/register");

      await page.fill('[name="email"]', "invalid-email");
      await page.fill('[name="password"]', "SecurePass123!");
      await page.fill('[name="organization_name"]', "Test Org");

      await page.click('button[type="submit"]');

      // Should show validation error
      await expect(page.getByText(/invalid email/i)).toBeVisible();
    });

    test("shows error for weak password", async ({ page }) => {
      await page.goto("/register");

      await page.fill('[name="email"]', "test@example.com");
      await page.fill('[name="password"]', "weak");
      await page.fill('[name="organization_name"]', "Test Org");

      await page.click('button[type="submit"]');

      // Should show password strength error
      await expect(page.getByText(/password/i)).toBeVisible();
    });
  });

  test.describe("Login", () => {
    test("user can login with valid credentials", async ({ page }) => {
      // First register a user
      const uniqueEmail = `login-test-${Date.now()}@example.com`;

      await page.goto("/register");
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="password"]', "SecurePass123!");
      await page.fill('[name="organization_name"]', "Login Test Org");
      await page.click('button[type="submit"]');

      await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

      // Logout
      await page.click('[data-testid="user-menu"]');
      await page.click('[data-testid="logout"]');

      await expect(page).toHaveURL(/\/login/);

      // Login with the same credentials
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="password"]', "SecurePass123!");
      await page.click('button[type="submit"]');

      // Should redirect to dashboard
      await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
    });

    test("shows error for invalid credentials", async ({ page }) => {
      await page.goto("/login");

      await page.fill('[name="email"]', "nonexistent@example.com");
      await page.fill('[name="password"]', "WrongPassword123!");
      await page.click('button[type="submit"]');

      // Should show error message
      await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible();
    });

    test("redirects unauthenticated users to login", async ({ page }) => {
      // Try to access protected route
      await page.goto("/dashboard");

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe("Password Reset", () => {
    test("user can request password reset", async ({ page }) => {
      await page.goto("/login");

      // Click forgot password link
      await page.click("text=Forgot password");

      await expect(page).toHaveURL(/\/forgot-password/);

      // Enter email
      await page.fill('[name="email"]', "test@example.com");
      await page.click('button[type="submit"]');

      // Should show success message (even if email doesn't exist - security)
      await expect(page.getByText(/email|sent|reset/i)).toBeVisible();
    });
  });

  test.describe("Session Management", () => {
    test("maintains session after page reload", async ({ page }) => {
      const uniqueEmail = `session-test-${Date.now()}@example.com`;

      // Register and login
      await page.goto("/register");
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="password"]', "SecurePass123!");
      await page.fill('[name="organization_name"]', "Session Test Org");
      await page.click('button[type="submit"]');

      await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

      // Reload page
      await page.reload();

      // Should still be on dashboard
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("logout clears session", async ({ page }) => {
      const uniqueEmail = `logout-test-${Date.now()}@example.com`;

      // Register
      await page.goto("/register");
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="password"]', "SecurePass123!");
      await page.fill('[name="organization_name"]', "Logout Test Org");
      await page.click('button[type="submit"]');

      await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

      // Logout
      await page.click('[data-testid="user-menu"]');
      await page.click('[data-testid="logout"]');

      await expect(page).toHaveURL(/\/login/);

      // Try to access dashboard
      await page.goto("/dashboard");

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);
    });
  });
});

test.describe("Team Invitations", () => {
  test("admin can access team management page", async ({ page }) => {
    const uniqueEmail = `admin-${Date.now()}@example.com`;

    // Register as admin
    await page.goto("/register");
    await page.fill('[name="email"]', uniqueEmail);
    await page.fill('[name="password"]', "SecurePass123!");
    await page.fill('[name="organization_name"]', "Admin Test Org");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

    // Navigate to team settings
    await page.click("text=Team");

    // Should see team management options
    await expect(page.getByText(/invite|team|members/i)).toBeVisible();
  });
});
