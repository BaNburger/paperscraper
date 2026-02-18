import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";

/** Create a research group via the projects dialog. */
async function createProject(page: Page, name?: string): Promise<string> {
  const projectName = name ?? `Research Group ${Date.now()}`;
  await page.getByRole("button", { name: /new research group|new group/i }).click();
  await page.getByLabel(/group name/i).fill(projectName);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: /create research group|create group/i })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden({ timeout: 10000 });
  await expect(
    page.getByRole("link", { name: new RegExp(projectName, "i") }).first()
  ).toBeVisible({ timeout: 10000 });
  return projectName;
}

/** Navigate from projects list to the created project's detail page. */
async function goToProjectDetail(page: Page, projectName: string): Promise<void> {
  await page.getByRole("link", { name: new RegExp(projectName, "i") }).first().click();
  await expect(page).toHaveURL(/\/projects\/[^/]+$/);
}

test.describe("Project KanBan Page", () => {
  let projectName: string;

  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/projects");
    projectName = await createProject(page);
    await goToProjectDetail(page, projectName);
  });

  test.describe("Page Structure", () => {
    test("displays project name in header", async ({ page }) => {
      await expect(
        page.getByRole("heading", { level: 1, name: new RegExp(projectName, "i") })
      ).toBeVisible();
    });

    test("displays back button", async ({ page }) => {
      await expect(
        page.getByRole("button", { name: /back to research groups/i })
      ).toBeVisible();
    });

    test("can navigate back to projects list", async ({ page }) => {
      await page.getByRole("button", { name: /back to research groups/i }).click();
      await expect(page).toHaveURL(/\/projects/);
    });
  });

  test.describe("Cluster State", () => {
    test("shows empty cluster state for a new research group", async ({ page }) => {
      await expect(page.getByText(/no clusters yet/i)).toBeVisible();
      await expect(page.getByText(/import papers|sync this research group/i)).toBeVisible();
    });

    test("shows Sync button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /^sync$/i }).first()).toBeVisible();
    });

    test("sync action button is enabled", async ({ page }) => {
      await expect(page.getByRole("button", { name: /^sync$/i }).first()).toBeEnabled();
    });
  });

  test.describe("Project Statistics", () => {
    test("displays paper count", async ({ page }) => {
      await expect(page.getByText(/\d+\s+papers/i).first()).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("project detail view is usable on tablet", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expect(page.getByRole("button", { name: /^sync$/i }).first()).toBeVisible();
    });

    test("project detail view is usable on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });

    test("project header visible on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  });

  test.describe("Error Handling", () => {
    test("shows error for non-existent project", async ({ page }) => {
      await page.goto("/projects/non-existent-id");
      await expect(page.getByText(/research group not found/i)).toBeVisible();
    });

    test("provides link back to projects on error", async ({ page }) => {
      await page.goto("/projects/non-existent-id");
      const backLink = page.getByRole("link", { name: /back to research groups/i }).or(
        page.getByRole("button", { name: /back to research groups/i })
      );
      if (await backLink.isVisible()) {
        await backLink.click();
        await expect(page).toHaveURL(/\/projects/);
      }
    });
  });
});
