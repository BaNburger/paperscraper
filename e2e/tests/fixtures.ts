import { test as base, expect, Page } from "@playwright/test";

export function generateTestUser() {
  const timestamp = Date.now();
  return {
    fullName: `Test User ${timestamp}`,
    email: `test-${timestamp}@example.com`,
    password: "SecurePass123!",
    organizationName: `Test Org ${timestamp}`,
  };
}

// Accepts "/" (home), "/dashboard", or "/onboarding" as valid post-auth destinations
const AUTHENTICATED_URL_PATTERN = /localhost:3000\/?$|\/dashboard|\/onboarding/;

/**
 * Register a new user with retry logic for transient 500 errors under parallel load.
 */
export async function registerUser(
  page: Page,
  user: { fullName: string; email: string; password: string; organizationName: string },
  retries = 2
) {
  let currentUser = { ...user };

  for (let attempt = 0; attempt <= retries; attempt++) {
    await page.goto("/register");
    await page.fill('[name="full_name"]', currentUser.fullName);
    await page.fill('[name="email"]', currentUser.email);
    await page.fill('[name="organization_name"]', currentUser.organizationName);
    await page.fill('[name="password"]', currentUser.password);
    await page.click('button[type="submit"]');

    try {
      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, { timeout: 15000 });
      return;
    } catch (error) {
      if (attempt === retries) {
        throw new Error(
          `Registration failed after ${retries + 1} attempts. Last URL: ${page.url()}. Error: ${error}`
        );
      }
      // Generate fresh credentials for retry (original email may now exist)
      const retryTimestamp = Date.now();
      currentUser = {
        ...user,
        email: `test-${retryTimestamp}@example.com`,
        fullName: `Test User ${retryTimestamp}`,
        organizationName: `Test Org ${retryTimestamp}`,
      };
      await page.waitForTimeout(500);
    }
  }
}

export async function loginUser(
  page: Page,
  credentials: { email: string; password: string }
) {
  await page.goto("/login");
  await page.fill('[name="email"]', credentials.email);
  await page.fill('[name="password"]', credentials.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, { timeout: 15000 });
}

export const test = base.extend<{
  authenticatedPage: Page;
  testUser: { fullName: string; email: string; password: string; organizationName: string };
}>({
  testUser: async ({}, use) => {
    const user = generateTestUser();
    await use(user);
  },
  authenticatedPage: async ({ page, testUser }, use) => {
    await registerUser(page, testUser);
    await use(page);
  },
});

export { expect, Page };
