import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

const firstProjectLink = (page: Page) =>
  page.locator('main a[href^="/projects/"]:not([href="/projects"])').first();

/** Create a research group via the dialog UI. Returns the group name. */
async function createProject(page: Page, name?: string): Promise<string> {
  const projectName = name ?? `Research Group ${Date.now()}`;
  await page.getByRole("button", { name: /new research group/i }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByLabel(/group name/i).fill(projectName);
  await page.getByLabel(/description/i).fill("Test description");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: /create research group/i })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  await expect(firstProjectLink(page)).toBeVisible({ timeout: 7000 });
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
      await expect(
        page.getByRole("heading", { level: 1, name: /research groups/i })
      ).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(
        page.getByText(/discover and track research groups.*publications/i)
      ).toBeVisible();
    });

    test("displays New Research Group button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /new research group/i })
      ).toBeVisible();
    });
  });

  test.describe("Empty State", () => {
    test("shows empty state when no groups", async ({ page }) => {
      await expect(page.getByText(/no research groups yet/i)).toBeVisible();
    });

    test("shows helpful description in empty state", async ({ page }) => {
      await expect(
        page.getByText(/search for an institution|start tracking/i)
      ).toBeVisible();
    });

    test("shows Create Research Group button in empty state", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /create research group/i })
      ).toBeVisible();
    });
  });

  test.describe("Create Group Dialog", () => {
    test("opens create dialog when clicking New Research Group", async ({ page }) => {
      await page.getByRole("button", { name: /new research group/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(page.getByText(/create research group/i).first()).toBeVisible();
    });

    test("dialog has group name field", async ({ page }) => {
      await page.getByRole("button", { name: /new research group/i }).click();
      await expect(page.getByLabel(/group name/i)).toBeVisible();
    });

    test("dialog has description field", async ({ page }) => {
      await page.getByRole("button", { name: /new research group/i }).click();
      await expect(page.getByLabel(/description/i)).toBeVisible();
    });

    test("dialog shows institution and author tabs", async ({ page }) => {
      await page.getByRole("button", { name: /new research group/i }).click();
      await expect(page.getByRole("button", { name: /institution/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /author/i })).toBeVisible();
    });

    test("can close dialog with Cancel button", async ({ page }) => {
      await page.getByRole("button", { name: /new research group/i }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByRole("dialog")).toBeHidden();
    });

    test("can create a new research group", async ({ page }) => {
      const projectName = `Test Group ${Date.now()}`;
      await createProject(page, projectName);
      await expect(page.getByText(projectName).first()).toBeVisible({ timeout: 7000 });
    });

    test("validates required group name", async ({ page }) => {
      await page.getByRole("button", { name: /new research group/i }).click();
      await expect(page.getByLabel(/group name/i)).toHaveAttribute("required");
    });
  });

  test.describe("Group Cards", () => {
    test.beforeEach(async ({ page }) => {
      await createProject(page);
    });

    test("displays group cards after creation", async ({ page }) => {
      await expect(firstProjectLink(page)).toBeVisible();
    });

    test("shows sync status badge", async ({ page }) => {
      await expect(page.getByText(/idle|ready|importing|failed|clustering/i).first()).toBeVisible();
    });

    test("shows paper count", async ({ page }) => {
      await expect(page.getByText(/\d+\s+papers/i).first()).toBeVisible();
    });

    test("shows cluster count", async ({ page }) => {
      await expect(page.getByText(/\d+\s+clusters/i).first()).toBeVisible();
    });

    test("can click group to view details", async ({ page }) => {
      await firstProjectLink(page).click();
      await expect(page).toHaveURL(/\/projects\/.+/);
    });
  });

  test.describe("Delete Group", () => {
    test.beforeEach(async ({ page }) => {
      await createProject(page, `Delete Group ${Date.now()}`);
    });

    test("shows delete button on hover", async ({ page }) => {
      const groupCard = page.locator(".group.relative").first();
      await groupCard.hover();
      await expect(page.getByRole("button", { name: /delete research group/i })).toBeVisible();
    });

    test("opens confirmation dialog when clicking delete", async ({ page }) => {
      const groupCard = page.locator(".group.relative").first();
      await groupCard.hover();
      await page.getByRole("button", { name: /delete research group/i }).click();

      await expect(page.getByText(/are you sure/i)).toBeVisible();
      await expect(page.getByText(/all.*removed|all cluster data will be removed/i)).toBeVisible();
    });

    test("can cancel delete", async ({ page }) => {
      const groupCard = page.locator(".group.relative").first();
      await groupCard.hover();
      await page.getByRole("button", { name: /delete research group/i }).click();
      await page.getByRole("button", { name: /cancel/i }).click();
      await expect(page.getByText(/are you sure/i)).toBeHidden();
    });

    test("can confirm delete", async ({ page }) => {
      const groupCard = page.locator(".group.relative").first();
      await groupCard.hover();
      await page.getByRole("button", { name: /delete research group/i }).click();

      await page
        .getByRole("dialog")
        .getByRole("button", { name: /^delete$/i })
        .click();

      await expect(page.getByText(/no research groups yet/i)).toBeVisible({
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

      const hasError = await page
        .getByText(/failed to load research groups/i)
        .isVisible()
        .catch(() => false);
      const hasEmptyState = await page
        .getByText(/no research groups yet/i)
        .isVisible()
        .catch(() => false);

      expect(hasError || hasEmptyState).toBeTruthy();
    });
  });
});
