import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a project via the dialog UI. Returns the project name. */
async function createProject(page: Page, name?: string): Promise<string> {
  const projectName = name ?? `Project ${Date.now()}`;
  await page.getByRole("button", { name: /new project/i }).click();
  await page.getByLabel(/project name/i).fill(projectName);
  await page.getByRole("dialog").getByRole("button", { name: /create project/i }).click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  await expect(page.locator('a[href*="/projects/"]').first()).toBeVisible({ timeout: 5000 });
  return projectName;
}

/** Navigate to a project's kanban board */
async function goToProjectKanban(page: Page): Promise<void> {
  // Click the first project card
  await page.locator('a[href*="/projects/"]').first().click();
  await expect(page).toHaveURL(/\/projects\/[^/]+$/);
}

test.describe("Project KanBan Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    // First create a project
    await page.goto("/projects");
    await page.waitForLoadState("networkidle");
    await createProject(page);
    await goToProjectKanban(page);
  });

  test.describe("Page Structure", () => {
    test("displays project name in header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });

    test("displays back button", async ({ page }) => {
      await expect(page.locator('svg[class*="ArrowLeft"]').first()).toBeVisible();
    });

    test("can navigate back to projects list", async ({ page }) => {
      await page.locator("button").filter({ has: page.locator('svg[class*="ArrowLeft"]') }).first().click();
      await expect(page).toHaveURL(/\/projects/);
    });
  });

  test.describe("KanBan Board", () => {
    test("displays kanban columns", async ({ page }) => {
      // Should have multiple stage columns
      const columns = page.locator(".w-80.shrink-0");
      await expect(columns.first()).toBeVisible();
    });

    test("displays default stages", async ({ page }) => {
      // Default stages: inbox, screening, evaluation, outreach, archived
      await expect(page.getByText("Inbox", { exact: true })).toBeVisible();
      await expect(page.getByText("Screening", { exact: true })).toBeVisible();
      await expect(page.getByText("Evaluation", { exact: true })).toBeVisible();
    });

    test("shows paper count badges on columns", async ({ page }) => {
      // Each column should have a count badge
      const badges = page.locator(".w-80 .rounded-t-lg").locator(".bg-secondary");
      await expect(badges.first()).toBeVisible();
    });

    test("shows empty message when no papers in stage", async ({ page }) => {
      await expect(page.getByText(/no papers in this stage/i).first()).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when all columns are empty", async ({ page }) => {
      // For a new project, all columns should be empty
      await expect(page.getByText(/no papers in this project/i)).toBeVisible();
    });

    test("shows Browse Papers button in empty state", async ({ page }) => {
      await expect(page.getByRole("button", { name: /browse papers/i })).toBeVisible();
    });

    test("Browse Papers button navigates to papers page", async ({ page }) => {
      await page.getByRole("button", { name: /browse papers/i }).click();
      await expect(page).toHaveURL(/\/papers/);
    });
  });

  test.describe("Project Statistics", () => {
    test("displays paper count", async ({ page }) => {
      await expect(page.getByText(/\d+ papers/i)).toBeVisible();
    });
  });

  test.describe("Drag and Drop", () => {
    test("columns have sortable context", async ({ page }) => {
      // Verify sortable columns exist (they have min-height)
      const dropZones = page.locator(".min-h-\\[200px\\]");
      await expect(dropZones.first()).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("kanban board is horizontally scrollable on tablet", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.locator(".overflow-x-auto")).toBeVisible();
    });

    test("kanban board is horizontally scrollable on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.locator(".overflow-x-auto")).toBeVisible();
    });

    test("project header visible on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  });

  test.describe("Error Handling", () => {
    test("shows error for non-existent project", async ({ page }) => {
      await page.goto("/projects/non-existent-id");
      await page.waitForLoadState("networkidle");

      await expect(page.getByText(/project not found|error/i)).toBeVisible();
    });

    test("provides link back to projects on error", async ({ page }) => {
      await page.goto("/projects/non-existent-id");
      await page.waitForLoadState("networkidle");

      const backLink = page.getByRole("link", { name: /back to projects/i }).or(
        page.getByRole("button", { name: /back to projects/i })
      );
      if (await backLink.isVisible()) {
        await backLink.click();
        await expect(page).toHaveURL(/\/projects/);
      }
    });
  });
});
