import { test as base, expect, Page } from "@playwright/test";

function uniqueSeed(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function generateTestUser() {
  const timestamp = uniqueSeed();
  return {
    fullName: `Test User ${timestamp}`,
    email: `test-${timestamp}@example.com`,
    password: "SecurePass123!",
    organizationName: `Test Org ${timestamp}`,
  };
}

// Accept any host, with "/", "/dashboard", or "/onboarding" as valid post-auth destinations.
const AUTHENTICATED_URL_PATTERN =
  /^https?:\/\/[^/]+(?:\/?$|\/dashboard(?:[/?#]|$)|\/onboarding(?:[/?#]|$))/;
const AUTH_REDIRECT_TIMEOUT_MS = 30000;

async function waitForCookieValue(
  page: Page,
  cookieName: string,
  timeoutMs = 10000
): Promise<string | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const cookieValue = (await page.context().cookies()).find((cookie) => cookie.name === cookieName)
      ?.value;
    if (cookieValue) {
      return cookieValue;
    }
    await page.waitForTimeout(100);
  }
  return null;
}

async function expectAuthenticatedSession(page: Page): Promise<void> {
  await expect
    .poll(
      async () =>
        (await page.context().cookies()).some((cookie) => cookie.name === "ps_access_token"),
      { timeout: 15000 }
    )
    .toBe(true);

  await expect
    .poll(async () => {
      const response = await page.request.get("/api/v1/auth/me");
      return response.status();
    }, { timeout: 15000 })
    .toBe(200);
}

async function completeOnboardingIfNeeded(page: Page): Promise<void> {
  const csrfToken = await waitForCookieValue(page, "ps_csrf_token", 8000);
  if (!csrfToken) return;

  try {
    await page.request.post("/api/v1/auth/onboarding/complete", {
      headers: { "X-CSRF-Token": csrfToken },
    });
  } catch {
    // Best-effort for test stability; onboarding is not the subject of most E2E specs.
  }
}

async function tryRegisterViaApi(
  page: Page,
  user: { fullName: string; email: string; password: string; organizationName: string }
): Promise<boolean> {
  try {
    const response = await page.request.post("/api/v1/auth/register", {
      data: {
        full_name: user.fullName,
        email: user.email,
        password: user.password,
        organization_name: user.organizationName,
      },
    });

    if (response.status() < 200 || response.status() >= 300) {
      return false;
    }

    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60000 });
    await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
      timeout: AUTH_REDIRECT_TIMEOUT_MS,
    });
    await expectAuthenticatedSession(page);
    await completeOnboardingIfNeeded(page);
    return true;
  } catch {
    return false;
  }
}

/**
 * Register a new user with retry logic for transient 500 errors under parallel load.
 */
export async function registerUser(
  page: Page,
  user: { fullName: string; email: string; password: string; organizationName: string },
  retries = 1
) {
  let currentUser = { ...user };

  for (let attempt = 0; attempt <= retries; attempt++) {
    const apiRegistrationWorked = await tryRegisterViaApi(page, currentUser);
    if (apiRegistrationWorked) {
      return;
    }

    await page.goto("/register", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.fill('[name="full_name"]', currentUser.fullName);
    await page.fill('[name="email"]', currentUser.email);
    await page.fill('[name="organization_name"]', currentUser.organizationName);
    await page.fill('[name="password"]', currentUser.password);
    await page.click('button[type="submit"]');

    try {
      await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
        timeout: AUTH_REDIRECT_TIMEOUT_MS,
      });
      await expectAuthenticatedSession(page);
      await completeOnboardingIfNeeded(page);
      return;
    } catch (error) {
      if (attempt === retries) {
        throw new Error(
          `Registration failed after ${retries + 1} attempts. Last URL: ${page.url()}. Error: ${error}`
        );
      }
      // Generate fresh credentials for retry (original email may now exist)
      const retryTimestamp = uniqueSeed();
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
  await page.goto("/login", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.fill('[name="email"]', credentials.email);
  await page.fill('[name="password"]', credentials.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(AUTHENTICATED_URL_PATTERN, {
    timeout: AUTH_REDIRECT_TIMEOUT_MS,
  });
  await expectAuthenticatedSession(page);
  await completeOnboardingIfNeeded(page);
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
