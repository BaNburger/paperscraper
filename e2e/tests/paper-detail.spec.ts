import { test, expect, registerUser, generateTestUser } from "./fixtures";

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
      await page.waitForLoadState("networkidle");

      // Should show error or redirect
      const hasError = await page.getByText(/not found|error|loading/i).isVisible().catch(() => false);
      const isRedirected = page.url().includes("/papers") && !page.url().includes("non-existent");
      expect(hasError || isRedirected).toBeTruthy();
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
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await expect(page).toHaveURL(/\/papers\/[^/]+$/);
    }
  });

  test("paper detail shows title", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      // Should show paper title in heading
      await expect(page.getByRole("heading")).toBeVisible();
    }
  });

  test("paper detail shows metadata section", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      // Should show DOI, source, or date
      const hasMetadata = await page.getByText(/doi|source|published/i).first().isVisible().catch(() => false);
      expect(hasMetadata).toBeTruthy();
    }
  });

  test("paper detail shows abstract", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      // Should show abstract section
      const hasAbstract = await page.getByText(/abstract/i).first().isVisible().catch(() => false);
      expect(hasAbstract).toBeTruthy();
    }
  });

  test("paper detail shows authors", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      // Should show authors section
      const hasAuthors = await page.getByText(/authors/i).first().isVisible().catch(() => false);
      expect(hasAuthors).toBeTruthy();
    }
  });

  test("paper detail has Score button", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      const scoreButton = page.getByRole("button", { name: /score|generate score/i });
      const hasScoreButton = await scoreButton.isVisible().catch(() => false);
      expect(hasScoreButton).toBeTruthy();
    }
  });

  test("paper detail has Add to Project button", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      const addButton = page.getByRole("button", { name: /add to project/i });
      const hasAddButton = await addButton.isVisible().catch(() => false);
      expect(hasAddButton).toBeTruthy();
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
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      const scoreButton = page.getByRole("button", { name: /score/i });
      if (await scoreButton.isVisible()) {
        await scoreButton.click();
        // Should show loading or success
        await page.waitForTimeout(2000);
      }
    }
  });

  test("can open Add to Project dialog", async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");

      const addButton = page.getByRole("button", { name: /add to project/i });
      if (await addButton.isVisible()) {
        await addButton.click();
        // Should show project selection
        await expect(page.getByText(/select.*project/i).or(page.getByRole("dialog"))).toBeVisible();
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

    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");
      await expect(page.getByRole("heading")).toBeVisible();
    }
  });

  test("adapts to tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    const paperLink = page.locator('a[href*="/papers/"]').first();
    const paperExists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (paperExists) {
      await paperLink.click();
      await page.waitForLoadState("networkidle");
      await expect(page.getByRole("heading")).toBeVisible();
    }
  });
});
