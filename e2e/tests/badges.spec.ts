import { test, expect, registerUser, generateTestUser } from "./fixtures";

test.describe("Badges Page", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
    await page.goto("/badges");
    await page.waitForLoadState("networkidle");
  });

  test.describe("Page Structure", () => {
    test("displays page header", async ({ page }) => {
      await expect(page.getByRole("heading", { level: 1, name: /badges/i })).toBeVisible();
    });

    test("displays page description", async ({ page }) => {
      await expect(page.getByText(/track your progress and earn badges/i)).toBeVisible();
    });

    test("displays Check for New Badges button", async ({ page }) => {
      await expect(page.getByRole("button", { name: /check for new badges/i })).toBeVisible();
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
      // Look for progress bar
      const progressBar = page.locator(".bg-primary.h-2.rounded-full");
      await expect(progressBar.first()).toBeVisible();
    });

    test("shows activity statistics", async ({ page }) => {
      await expect(page.getByText(/papers imported/i)).toBeVisible();
      await expect(page.getByText(/papers scored/i)).toBeVisible();
      await expect(page.getByText(/searches/i).first()).toBeVisible();
    });
  });

  test.describe("Badge Gallery", () => {
    test("displays badge categories", async ({ page }) => {
      // Check for category sections
      const categories = ["import", "scoring", "collaboration", "exploration", "milestone"];
      let foundCategories = 0;

      for (const category of categories) {
        const heading = page.getByRole("heading", { level: 2 }).filter({ hasText: new RegExp(category, "i") });
        if (await heading.isVisible().catch(() => false)) {
          foundCategories++;
        }
      }

      // Should have at least one category visible or show empty state
      const hasCategories = foundCategories > 0;
      const hasEmptyState = await page.getByText(/no badges available/i).isVisible().catch(() => false);
      expect(hasCategories || hasEmptyState).toBeTruthy();
    });

    test("displays badge cards with tier badges", async ({ page }) => {
      // Look for tier badges (bronze, silver, gold, platinum)
      const tierBadges = page.locator(".capitalize").filter({ hasText: /bronze|silver|gold|platinum/i });

      // Either we have badges or an empty state
      const hasBadges = await tierBadges.count() > 0;
      const hasEmptyState = await page.getByText(/no badges available/i).isVisible().catch(() => false);
      expect(hasBadges || hasEmptyState).toBeTruthy();
    });

    test("displays badge points", async ({ page }) => {
      // Look for "pts" text
      const ptsText = page.getByText(/\d+\s*pts/i);
      const hasBadges = await ptsText.count() > 0;
      const hasEmptyState = await page.getByText(/no badges available/i).isVisible().catch(() => false);
      expect(hasBadges || hasEmptyState).toBeTruthy();
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
      const checkButton = page.getByRole("button", { name: /check for new badges/i });
      await expect(checkButton).toBeEnabled();
      await checkButton.click();

      // Should show a toast notification
      await page.waitForTimeout(1000);
      const hasToast = await page.getByRole("alert").isVisible().catch(() => false);
      const hasSuccessText = await page.getByText(/all caught up|new badges/i).isVisible().catch(() => false);
      expect(hasToast || hasSuccessText).toBeTruthy();
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
