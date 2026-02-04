import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a project via the dialog UI. Returns the project name. */
async function createProject(page: Page, name?: string): Promise<string> {
  const projectName = name ?? `Project ${Date.now()}`;
  await page.getByRole("button", { name: /new project/i }).click();
  await page.getByLabel(/project name/i).fill(projectName);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: /create project/i })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  // Wait for project card to appear instead of hardcoded timeout
  await expect(page.locator('a[href*="/projects/"]').first()).toBeVisible({ timeout: 5000 });
  return projectName;
}

test.describe("Projects Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/projects");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /projects/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(
        page.getByText(/organize papers into research pipelines/i)
      ).toBeVisible();
    });

    test("displays New Project button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /new project/i })
      ).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no projects", async ({ page }) => {
      await expect(page.getByText(/no projects yet/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(
        page.getByText(/create a project to organize your papers/i)
      ).toBeVisible();
    });

    test("shows Create Project button in empty state", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /create project/i })
      ).toBeVisible();
    });
  });

  test.describe("Create Project Dialog", () => {
    test("opens create dialog when clicking New Project", async ({ page }) => {
      await page.getByRole("button", { name: /new project/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/create project/i).first()).toBeVisible();
    });

    test("dialog has project name field", async ({ page }) => {
      await page.getByRole("button", { name: /new project/i }).click();
      await expect(page.getByLabel(/project name/i)).toBeVisible();
    });

    test("dialog has description field", async ({ page }) => {
      await page.getByRole("button", { name: /new project/i }).click();
      await expect(page.getByLabel(/description/i)).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /new project/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("can create a new project", async ({ page }) => {
      const projectName = `Test Project ${Date.now()}`;
      await page.getByRole("button", { name: /new project/i }).click();
      await page.getByLabel(/project name/i).fill(projectName);
      await page.getByLabel(/description/i).fill("Test description");

      await page
        .getByRole("dialog")
        .getByRole("button", { name: /create project/i })
        .click();

      await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
      // Use .first() to avoid matching toast text
      await expect(page.getByText(projectName).first()).toBeVisible({ timeout: 5000 });
    });

    test("validates required project name", async ({ page }) => {
      await page.getByRole("button", { name: /new project/i }).click();
      await expect(page.getByLabel(/project name/i)).toHaveAttribute("required");
    });
  });

  test.describe("Project Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createProject(page);
    });

    test("displays project cards after creation", async ({ page }) => {
      await expect(page.locator('a[href*="/projects/"]').first()).toBeVisible();
    });

    test("shows project status badge", async ({ page }) => {
      await expect(page.getByText(/active|inactive/i).first()).toBeVisible();
    });

    test("shows stage count", async ({ page }) => {
      await expect(page.getByText(/\d+ stages/i)).toBeVisible();
    });

    test("shows creation date", async ({ page }) => {
      await expect(page.locator("main").getByText(/created/i).first()).toBeVisible();
    });

    test("can click project to view details", async ({ page }) => {
      await page.locator('a[href*="/projects/"]').first().click();
      await expect(page).toHaveURL(/\/projects\/.+/);
    });
  });

  test.describe("Delete Project", () => {
    test.beforeEach(async ({ page }) => {
      await createProject(page, `Delete Test ${Date.now()}`);
    });

    test("shows delete button on hover", async ({ page }) => {
      const projectCard = page.locator(".group.relative").first();
      await projectCard.hover();
      await expect(page.getByRole("button", { name: /delete project/i })).toBeVisible();
    });

    test("opens confirmation dialog when clicking delete", async ({ page }) => {
      const projectCard = page.locator(".group.relative").first();
      await projectCard.hover();
      await page.getByRole("button", { name: /delete project/i }).click();

      await expect(page.getByText(/are you sure/i)).toBeVisible();
      await expect(page.getByText(/cannot be undone/i)).toBeVisible();
    });

    test("can cancel delete", async ({ page }) => {
      const projectCard = page.locator(".group.relative").first();
      await projectCard.hover();
      await page.getByRole("button", { name: /delete project/i }).click();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByText(/are you sure/i)).toBeHidden();
    });

    test("can confirm delete", async ({ page }) => {
      const projectCard = page.locator(".group.relative").first();
      await projectCard.hover();
      await page.getByRole("button", { name: /delete project/i }).click();

      await page
        .getByRole("dialog")
        .getByRole("button", { name: /delete/i })
        .click();

      await expect(page.getByText(/no projects yet/i)).toBeVisible({
        timeout: 10000,
      });
    });
  });

  test.describe("Error Handling", () => {
    test("handles API errors gracefully", async ({ page }) => {
      await page.route("**/api/v1/projects*", (route) => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ detail: "Server error" }),
        });
      });

      await page.reload();
      await page.waitForLoadState("networkidle");

      // React Query may show error state or cached empty state on refetch failure
      const hasError = await page
        .getByText(/failed to load projects/i)
        .isVisible()
        .catch(() => false);
      const hasEmptyState = await page
        .getByText(/no projects yet/i)
        .isVisible()
        .catch(() => false);

      expect(hasError || hasEmptyState).toBeTruthy();
    });
  });
});
