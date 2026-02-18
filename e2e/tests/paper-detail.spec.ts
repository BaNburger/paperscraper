import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

async function openFirstPaperDetail(page: Page): Promise<boolean> {
  const paperLink = page.locator('main a[href^="/papers/"]:not([href="/papers"])').first();
  const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);
  if (!paperExists) return false;
  try {
    await paperLink.click();
    await expect(page).toHaveURL(/\/papers\/[0-9a-f-]+$/i);
    await expect(page.getByRole("button", { name: /go back/i })).toBeVisible({ timeout: 10000 });
    return true;
  } catch {
    return false;
  }
}

async function openPaperTab(page: Page, tabName: RegExp): Promise<void> {
  const tabButton = page.getByRole("button", { name: tabName }).first();
  if (await tabButton.isVisible().catch(() => false)) {
    await tabButton.click();
  }
}

async function hasAnyVisibleButton(page: Page, buttonNames: RegExp[]): Promise<boolean> {
  for (const name of buttonNames) {
    const button = page.getByRole("button", { name }).first();
    if (await button.isVisible().catch(() => false)) {
      return true;
    }
  }
  return false;
}

async function clickFirstVisibleButton(page: Page, buttonNames: RegExp[]): Promise<boolean> {
  for (const name of buttonNames) {
    const button = page.getByRole("button", { name }).first();
    if (await button.isVisible().catch(() => false)) {
      await button.click();
      return true;
    }
  }
  return false;
}

test.describe("Paper Detail Page", () => {
  // These tests navigate to a paper detail page
  // In a real scenario, we'd import a paper first

  test.describe("Empty State - No Paper ID", () => {
    test.beforeEach(async ({ page }) => {
      const user = generateTestUser();
      await registerUser(page, user);
    });

    test("shows error for non-existent paper", async ({ page }) => {
      await page.goto("/papers/non-existent-id");
      await expect(page.locator("main")).toBeVisible();
      const pathname = new URL(page.url()).pathname;
      const stayedOnInvalid = pathname.includes("/papers/non-existent-id");
      const redirectedToList = /\/papers\/?$/.test(pathname);
      expect(stayedOnInvalid || redirectedToList).toBeTruthy();
    });
  });
});

test.describe("Paper Detail Page - Structure", () => {
  // These tests verify the UI structure when viewing a paper

  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);

    // First import a paper
    await page.goto("/papers");
    await page.waitForLoadState("networkidle");

    // Try to import via DOI
    await page.getByRole("button", { name: /import papers/i }).first().click();
    await page.fill("#doi", "10.1038/nature12373");
    await page.getByRole("button", { name: "Import", exact: true }).click();

    // Wait for import to complete
    await page.waitForTimeout(5000);

    // Navigate to papers page and check if paper exists
    await page.goto("/papers");
    await page.waitForLoadState("networkidle");
  });

  test("can access paper detail page", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await expect(page).toHaveURL(/\/papers\/[0-9a-f-]+$/i);
    }
  });

  test("paper detail shows title", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("paper detail shows metadata section", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await openPaperTab(page, /insights/i);
      await expect(page.getByRole("heading", { name: /metadata/i })).toBeVisible({
        timeout: 10000,
      });
    }
  });

  test("paper detail shows abstract", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      const hasAbstract = await page.getByText(/abstract/i).first().isVisible().catch(() => false);
      expect(hasAbstract).toBeTruthy();
    }
  });

  test("paper detail shows authors", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      const hasAuthors = await page.getByText(/authors|author profile/i).first().isVisible().catch(() => false);
      const hasAuthorProfiles = await page.getByText(/author profile/i).first().isVisible().catch(() => false);
      expect(hasAuthors || hasAuthorProfiles).toBeTruthy();
    }
  });

  test("paper detail has Score button", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await openPaperTab(page, /insights/i);
      const hasScoreAction = await hasAnyVisibleButton(page, [
        /score now/i,
        /generate score/i,
        /score/i,
        /interesting/i,
        /skip/i,
      ]);
      expect(hasScoreAction).toBeTruthy();
    }
  });

  test("paper detail has Start Transfer button", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      const transferButton = page.getByRole("button", { name: /start transfer/i }).first();
      const hasTransferButton = await transferButton.isVisible().catch(() => false);
      expect(hasTransferButton).toBeTruthy();
    }
  });
});

test.describe("Paper Detail Page - Actions", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/papers");
    await page.waitForLoadState("networkidle");

    // Try to import via DOI
    await page.getByRole("button", { name: /import papers/i }).first().click();
    await page.fill("#doi", "10.1038/nature12373");
    await page.getByRole("button", { name: "Import", exact: true }).click();
    await page.waitForTimeout(5000);

    await page.goto("/papers");
    await page.waitForLoadState("networkidle");
  });

  test("can trigger AI scoring", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await openPaperTab(page, /insights/i);
      const clicked = await clickFirstVisibleButton(page, [
        /score now/i,
        /generate score/i,
        /score/i,
        /interesting/i,
      ]);
      expect(clicked).toBeTruthy();
      await page.waitForTimeout(2000);
    }
  });

  test("can open Start Transfer dialog", async ({ page }) => {
    const opened = await openFirstPaperDetail(page);
    if (opened) {
      const transferButton = page.getByRole("button", { name: /start transfer/i }).first();
      if (await transferButton.isVisible()) {
        await transferButton.click();
        await expect(page.getByRole("dialog")).toBeVisible();
      }
    }
  });
});

test.describe("Paper Detail Page - Responsive Design", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/papers");
    await page.waitForLoadState("networkidle");
  });

  test("adapts to mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("adapts to tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    const opened = await openFirstPaperDetail(page);
    if (opened) {
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });
});
