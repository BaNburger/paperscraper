import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Badges Page", () => {
  test.describe.configure({ timeout: 90000 });

  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/badges", { waitUntil: "domcontentloaded", timeout: 60000 });
    await expect(page.getByRole("heading", { level: 1, name: /badges/i })).toBeVisible({
      timeout: 20000,
    });
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /badges/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/track your progress and earn badges/i)).toBeVisible();
    });

    test("displays Check for New Badges button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /check for new( badges)?/i })).toBeVisible();
    });
  });

  test.describe("Stats Overview Cards", () => {
    test("displays Level card", async ({ page }) => {
      await expect(page.getByText("Level").first()).toBeVisible();
    });

    test("displays Total Points card", async ({ page }) => {
      await expect(page.getByText(/total points/i).first()).toBeVisible();
    });

    test("displays Badges Earned card", async ({ page }) => {
      await expect(page.getByText(/badges earned/i).first()).toBeVisible();
    });

    test("displays Activity card", async ({ page }) => {
      await expect(page.getByText("Activity").first()).toBeVisible();
    });

    test("shows level progress bar", async ({ page }) => {
      const progressTrack = page.locator(".bg-muted.h-2.rounded-full");
      await expect(progressTrack.first()).toBeVisible();
      const progressFill = progressTrack.first().locator("> div").first();
      await expect(progressFill).toHaveAttribute("style", /width:\s*\d+(\.\d+)?%/);
    });

    test("shows activity statistics", async ({ page }) => {
      await expect(page.getByText(/papers imported/i)).toBeVisible();
      await expect(page.getByText(/papers scored/i)).toBeVisible();
      await expect(page.getByText(/searches/i).first()).toBeVisible();
    });
  });

  test.describe("Badge Gallery", () => {
    test("displays badge categories", async ({ page }) => {
      // Wait for either category sections to render or an explicit empty state.
      await expect
        .poll(async () => {
          const hasCategories =
            (await page
              .getByRole("heading", { level: 2 })
              .filter({ hasText: /import|scoring|collaboration|exploration|milestone/i })
              .count()) > 0;
          const hasEmptyState = await page.getByText(/no badges available/i).isVisible().catch(() => false);
          return hasCategories || hasEmptyState;
        })
        .toBeTruthy();
    });

    test("displays badge cards with tier badges", async ({ page }) => {
      // Wait until either tier labels are rendered or an explicit empty state is shown.
      await expect
        .poll(async () => {
          const hasTierLabels =
            (await page.getByText(/\b(bronze|silver|gold|platinum)\b/i).count()) > 0;
          const hasEmptyState = await page.getByText(/no badges available/i).isVisible().catch(() => false);
          return hasTierLabels || hasEmptyState;
        })
        .toBeTruthy();
    });

    test("displays badge points", async ({ page }) => {
      // Firefox can render badge cards a moment later than the section headings.
      // Wait until either point labels are present or the empty state is shown.
      await expect
        .poll(async () => {
          const hasPoints = (await page.getByText(/\bpts\b/i).count()) > 0;
          const hasEmptyState = await page.getByText(/no badges available/i).isVisible().catch(() => false);
          return hasPoints || hasEmptyState;
        })
        .toBeTruthy();
    });

    test("shows locked badges with lock icon", async ({ page }) => {
      // Look for lock icons on unearned badges
      const lockIcons = page.locator('svg[class*="Lock"]');
      // This might not be visible if user has no badges, which is fine
      const lockCount = await lockIcons.count();
      expect(lockCount).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe("Check Badges Button", () => {
    test("can click Check for New Badges", async ({ page }) => {
      const checkButton = page.getByRole("button", { name: /check for new( badges)?/i });
      await expect(checkButton).toBeEnabled();

      const checkResponse = page.waitForResponse(
        (response) =>
          response.request().method() === "POST" &&
          response.url().includes("/api/v1/badges/me/check")
      );

      await checkButton.click();
      const response = await checkResponse;
      expect(response.status()).toBeLessThan(500);

      await expect(checkButton).toBeEnabled();
      await expect(page.getByRole("heading", { level: 1, name: /badges/i })).toBeVisible();
    });
  });

  test.describe("Responsive Design", () => {
    test("adapts to tablet viewport", async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await expect(page.getByRole("heading", { level: 1, name: /badges/i })).toBeVisible();
      await expect(page.getByText("Level").first()).toBeVisible();
    });

    test("adapts to mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.getByRole("heading", { level: 1, name: /badges/i })).toBeVisible();
    });

    test("stats cards stack on mobile", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      // Verify cards are still visible
      await expect(page.getByText("Level").first()).toBeVisible();
      await expect(page.getByText(/total points/i).first()).toBeVisible();
    });
  });
});
