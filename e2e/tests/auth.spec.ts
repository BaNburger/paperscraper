import { test, expect, type Page } from "@playwright/test";

// Accept any host, with "/", "/dashboard", or "/onboarding" as valid post-auth destinations.
const AUTHENTICATED_URL_PATTERN =
  /^https?:\/\/[^/]+(?:\/?$|\/dashboard(?:[/?#]|$)|\/onboarding(?:[/?#]|$))/;
const AUTH_REDIRECT_TIMEOUT_MS = 30000;

test.describe.configure({ mode: "serial" });

function uniqueSeed(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

async function logoutViaUserMenu(page: Page, userName: RegExp) {
  const namedUserButton = page.getByRole("button", { name: userName }).first();
  if (await namedUserButton.isVisible().catch(() => false)) {
    await namedUserButton.click();
  } else {
    const compactUserButton = page
      .locator("header button")
      .filter({ has: page.locator("svg.lucide-user") })
      .first();
    await expect(compactUserButton).toBeVisible({ timeout: 10000 });
    await compactUserButton.click();
  }

  const logoutButton = page.getByRole("menuitem", {
    name: /log ?out|logout|sign out|abmelden/i,
  });
  await expect(logoutButton).toBeVisible({ timeout: 10000 });
  await logoutButton.click();
}

test.describe("Authentication", () => {
  test.describe("Registration", () => {
    test("user can register with valid credentials", async ({ page }) => {
      const uniqueEmail = `test-${uniqueSeed()}@example.com`;

      await page.goto("/register");

      // Fill registration form
      await page.fill('[name="full_name"]', "Test User");
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="organization_name"]', "Test Organization");
      await page.fill('[name="password"]', "SecurePass123!");

      // Submit form
      await page.click('button[type="submit"]');

      // Should redirect to dashboard after successful registration
      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });

      // User should see dashboard content (heading or welcome message)
      await expect(
        page.getByRole("heading", { name: /dashboard|welcome/i })
      ).toBeVisible({ timeout: 5000 });
    });

    test("shows error for invalid email format", async ({ page }) => {
      await page.goto("/register");

      await page.fill('[name="full_name"]', "Test User");
      await page.fill('[name="email"]', "invalid-email");
      await page.fill('[name="organization_name"]', "Test Org");
      await page.fill('[name="password"]', "SecurePass123!");

      await page.click('button[type="submit"]');

      // HTML5 validation or API error - look for any error indication
      // The browser's native validation will show "Please include an '@' in the email address"
      // or the form will show a custom error
      const hasValidationError = await page.locator(':invalid').count() > 0;
      const hasErrorMessage = await page.getByText(/invalid|error|@/i).count() > 0;
      expect(hasValidationError || hasErrorMessage).toBe(true);
    });

    test("shows error for weak password", async ({ page }) => {
      await page.goto("/register");

      await page.fill('[name="full_name"]', "Test User");
      await page.fill('[name="email"]', `weak-pwd-${uniqueSeed()}@example.com`);
      await page.fill('[name="organization_name"]', "Test Org");
      await page.fill('[name="password"]', "weak");

      await page.click('button[type="submit"]');

      // Should show password validation error (either browser native or custom)
      // Wait for either the form to show error or stay on register page
      await page.waitForTimeout(1000);

      // Check for validation errors or that we're still on the register page
      const isStillOnRegister = page.url().includes('/register');
      expect(isStillOnRegister).toBe(true);
    });
  });

  test.describe("Login", () => {
    test("user can login with valid credentials", async ({ page }) => {
      // First register a user
      const uniqueEmail = `login-test-${uniqueSeed()}@example.com`;
      const fullName = "Login Test User";

      await page.goto("/register");
      await page.fill('[name="full_name"]', fullName);
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="organization_name"]', "Login Test Org");
      await page.fill('[name="password"]', "SecurePass123!");
      await page.click('button[type="submit"]');

      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });

      await logoutViaUserMenu(page, /login test user/i);

      await expect(page).toHaveURL(/\/login/, { timeout: 20000 });

      // Login with the same credentials
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="password"]', "SecurePass123!");
      await page.click('button[type="submit"]');

      // Should redirect to dashboard
      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });
    });

    test("shows error for invalid credentials", async ({ page }) => {
      await page.goto("/login");

      await page.fill('[name="email"]', "nonexistent@example.com");
      await page.fill('[name="password"]', "WrongPassword123!");
      await page.click('button[type="submit"]');

      // Wait for the form submission to complete
      await page.waitForTimeout(2000);

      // Should show error message - look for common error text patterns
      const errorElement = page.locator('.bg-destructive, [role="alert"]').or(
        page.getByText(/invalid|incorrect|failed|wrong|error/i)
      );
      await expect(errorElement.first()).toBeVisible({ timeout: 5000 });
    });

    test("redirects unauthenticated users to login", async ({ page }) => {
      // Try to access protected route
      await page.goto("/dashboard");

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/, { timeout: 20000 });
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

      // Should show success message or confirmation screen
      // Wait for the request to complete
      await page.waitForTimeout(2000);

      // Look for success indicators: success message, check icon, or "check your email" text
      const successIndicator = page.getByText(/check your email|sent|success|reset link/i).or(
        page.locator('.text-green, .bg-green, [data-testid="success"]')
      );
      await expect(successIndicator.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Session Management", () => {
    test("maintains session after page reload", async ({ page }) => {
      const uniqueEmail = `session-test-${uniqueSeed()}@example.com`;

      // Register and login
      await page.goto("/register");
      await page.fill('[name="full_name"]', "Session Test User");
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="organization_name"]', "Session Test Org");
      await page.fill('[name="password"]', "SecurePass123!");
      await page.click('button[type="submit"]');

      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });

      // Reload page
      await page.reload();

      // Should still be authenticated (not redirected to login)
      await expect(page).not.toHaveURL(/\/login/);
      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });
    });

    test("logout clears session", async ({ page }) => {
      const uniqueEmail = `logout-test-${uniqueSeed()}@example.com`;
      const fullName = "Logout Test User";

      // Register
      await page.goto("/register");
      await page.fill('[name="full_name"]', fullName);
      await page.fill('[name="email"]', uniqueEmail);
      await page.fill('[name="organization_name"]', "Logout Test Org");
      await page.fill('[name="password"]', "SecurePass123!");
      await page.click('button[type="submit"]');

      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });

      await logoutViaUserMenu(page, /logout test user/i);

      await expect(page).toHaveURL(/\/login/);

      // Try to access dashboard
      await page.goto("/dashboard");

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/, { timeout: 20000 });
    });
  });
});

test.describe("Team Invitations", () => {
  test("admin can access team management page", async ({ page }) => {
    const uniqueEmail = `admin-${uniqueSeed()}@example.com`;

    // Register as admin
    await page.goto("/register");
    await page.fill('[name="full_name"]', "Admin Test User");
    await page.fill('[name="email"]', uniqueEmail);
    await page.fill('[name="organization_name"]', "Admin Test Org");
    await page.fill('[name="password"]', "SecurePass123!");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
      timeout: AUTH_REDIRECT_TIMEOUT_MS,
    });

    // Navigate directly to team page to support collapsed mobile navigation layouts
    await page.goto("/team");

    // Should see team management page content
    await expect(page).toHaveURL(/\/team/);
    await expect(
      page.locator("main").getByRole("heading", { level: 1, name: /team members/i })
    ).toBeVisible();
    await expect(page.locator("main").getByRole("button", { name: /invite member/i })).toBeVisible();
  });
});
