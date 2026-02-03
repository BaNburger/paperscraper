import { test, expect } from "@playwright/test";

test.describe("Papers", () => {
  // Setup: Register and login before each test
  test.beforeEach(async ({ page }) => {
    const uniqueEmail = `papers-test-${Date.now()}@example.com`;

    await page.goto("/register");
    await page.fill('[name="email"]', uniqueEmail);
    await page.fill('[name="password"]', "SecurePass123!");
    await page.fill('[name="organization_name"]', "Papers Test Org");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test.describe("Paper List", () => {
    test("can view papers list", async ({ page }) => {
      // Navigate to papers page
      await page.click("text=Papers");

      await expect(page).toHaveURL(/\/papers/);

      // Should see papers page header
      await expect(page.getByRole("heading", { name: /papers/i })).toBeVisible();
    });

    test("shows empty state when no papers", async ({ page }) => {
      await page.goto("/papers");

      // Should show empty state or import prompt
      await expect(page.getByText(/no papers|import|add/i)).toBeVisible();
    });
  });

  test.describe("Paper Import", () => {
    test("can access DOI import form", async ({ page }) => {
      await page.goto("/papers");

      // Look for import button
      await page.click("text=Import");

      // Should see import options
      await expect(page.getByText(/doi|arxiv|pubmed/i)).toBeVisible();
    });

    test("can import paper by DOI", async ({ page }) => {
      await page.goto("/papers");

      // Click import
      await page.click("text=Import");

      // Select DOI import
      await page.click("text=DOI");

      // Enter a test DOI
      await page.fill('[name="doi"]', "10.1038/nature12373");
      await page.click('button[type="submit"]');

      // Should show loading or success state
      await expect(
        page.getByText(/importing|loading|success|added/i)
      ).toBeVisible({ timeout: 15000 });
    });
  });

  test.describe("Paper Detail", () => {
    test("can view paper details after import", async ({ page }) => {
      // Import a paper first
      await page.goto("/papers");
      await page.click("text=Import");
      await page.click("text=DOI");
      await page.fill('[name="doi"]', "10.1038/nature12373");
      await page.click('button[type="submit"]');

      // Wait for import
      await page.waitForTimeout(5000);

      // Refresh papers list
      await page.goto("/papers");

      // Click on the paper
      await page.click("article >> first");

      // Should see paper details
      await expect(page.getByText(/abstract|authors|doi/i)).toBeVisible();
    });
  });

  test.describe("Paper Actions", () => {
    test("can add paper to project", async ({ page }) => {
      // This test assumes a paper exists
      await page.goto("/papers");

      // Look for paper actions menu
      const paperCard = page.locator("article").first();
      if (await paperCard.isVisible()) {
        await paperCard.click();

        // Look for add to project option
        await page.click("text=Add to Project");

        // Should see project selection
        await expect(page.getByText(/select.*project/i)).toBeVisible();
      }
    });

    test("can trigger AI scoring", async ({ page }) => {
      await page.goto("/papers");

      const paperCard = page.locator("article").first();
      if (await paperCard.isVisible()) {
        await paperCard.click();

        // Look for score button
        await page.click("text=Score");

        // Should show scoring in progress or results
        await expect(page.getByText(/scoring|novelty|potential/i)).toBeVisible({
          timeout: 30000,
        });
      }
    });
  });
});

test.describe("Search", () => {
  test.beforeEach(async ({ page }) => {
    const uniqueEmail = `search-test-${Date.now()}@example.com`;

    await page.goto("/register");
    await page.fill('[name="email"]', uniqueEmail);
    await page.fill('[name="password"]', "SecurePass123!");
    await page.fill('[name="organization_name"]', "Search Test Org");
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
  });

  test("can access search functionality", async ({ page }) => {
    // Look for search input in header or navigation
    await page.click('[data-testid="search-input"]');

    // Should see search interface
    await expect(page.getByPlaceholder(/search/i)).toBeVisible();
  });

  test("can perform semantic search", async ({ page }) => {
    await page.goto("/search");

    // Enter search query
    await page.fill('[name="query"]', "machine learning drug discovery");

    // Select semantic search mode if available
    const semanticToggle = page.locator("text=Semantic");
    if (await semanticToggle.isVisible()) {
      await semanticToggle.click();
    }

    await page.click('button[type="submit"]');

    // Should show search results or no results message
    await expect(page.getByText(/results|no.*found/i)).toBeVisible({
      timeout: 15000,
    });
  });
});
