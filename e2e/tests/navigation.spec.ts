import { test, expect, registerUser, generateTestUser, Page } from "./fixtures";
import type { Locator } from "@playwright/test";

const MOBILE_BOTTOM_PATHS = new Set(["/", "/papers", "/projects", "/search"]);

function isDesktopLayout(page: Page): boolean {
  return (page.viewportSize()?.width ?? 1024) >= 768;
}

async function openMobileMenu(page: Page): Promise<void> {
  const dialog = page.getByRole("dialog");
  if (await dialog.isVisible().catch(() => false)) {
    return;
  }

  const mobileNav = page.getByRole("navigation", { name: /primary mobile navigation/i });
  const moreButton = mobileNav.getByRole("button", { name: /more/i }).first();
  await expect(moreButton).toBeVisible({ timeout: 10000 });
  await moreButton.click();
  await expect(dialog).toBeVisible({ timeout: 10000 });
}

async function expectNavLinkVisible(page: Page, path: string): Promise<void> {
  const desktopLink = page.locator(`aside a[href="${path}"]`).first();
  if (isDesktopLayout(page)) {
    await expect(desktopLink).toBeVisible({ timeout: 10000 });
    return;
  }

  const mobileNav = page.getByRole("navigation", { name: /primary mobile navigation/i });
  const mobileBottomLink = mobileNav.locator(`a[href="${path}"]`).first();
  if (MOBILE_BOTTOM_PATHS.has(path)) {
    await expect(mobileBottomLink).toBeVisible();
    return;
  }

  await openMobileMenu(page);
  await expect(page.getByRole("dialog").locator(`a[href="${path}"]`).first()).toBeVisible({
    timeout: 10000,
  });
}

async function clickNavLink(page: Page, path: string): Promise<void> {
  if (isDesktopLayout(page)) {
    const desktopLink = page.locator(`aside a[href="${path}"]`).first();
    await expect(desktopLink).toBeVisible({ timeout: 10000 });
    await desktopLink.click();
    return;
  }

  const mobileNav = page.getByRole("navigation", { name: /primary mobile navigation/i });
  const mobileBottomLink = mobileNav.locator(`a[href="${path}"]`).first();
  if (MOBILE_BOTTOM_PATHS.has(path)) {
    await mobileBottomLink.click();
    return;
  }

  await openMobileMenu(page);
  const menuLink = page.getByRole("dialog").locator(`a[href="${path}"]`).first();
  await expect(menuLink).toBeVisible({ timeout: 10000 });
  await menuLink.click();
  await page.getByRole("dialog").waitFor({ state: "hidden", timeout: 10000 }).catch(() => {});
}

async function expectLinkActive(link: Locator): Promise<void> {
  await expect
    .poll(async () => {
      const className = await link.getAttribute("class");
      const ariaCurrent = await link.getAttribute("aria-current");
      return Boolean(
        ariaCurrent === "page" ||
        (className && (className.includes("bg-primary") || className.includes("text-primary")))
      );
    })
    .toBe(true);
}

test.describe("Navigation & Layout", () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser();
    await registerUser(page, user);
  });

  test.describe("Sidebar Navigation", () => {
    test("displays all main navigation links", async ({ page }) => {
      await expectNavLinkVisible(page, "/");
      await expectNavLinkVisible(page, "/papers");
      await expectNavLinkVisible(page, "/projects");
      await expectNavLinkVisible(page, "/search");
      await expectNavLinkVisible(page, "/analytics");
    });

    test("displays bottom navigation links", async ({ page }) => {
      await expectNavLinkVisible(page, "/team");
      await expectNavLinkVisible(page, "/settings");
    });

    test("navigates to Papers page", async ({ page }) => {
      await clickNavLink(page, "/papers");
      await expect(page).toHaveURL(/\/papers/);
      await expect(page.getByRole("heading", { level: 1, name: /papers/i })).toBeVisible();
    });

    test("navigates to Projects page", async ({ page }) => {
      await clickNavLink(page, "/projects");
      await expect(page).toHaveURL(/\/projects/);
      await expect(page.getByRole("heading", { level: 1, name: /research groups/i })).toBeVisible();
    });

    test("navigates to Search page", async ({ page }) => {
      await clickNavLink(page, "/search");
      await expect(page).toHaveURL(/\/search/);
      await expect(page.getByRole("heading", { level: 1, name: /search/i })).toBeVisible();
    });

    test("navigates to Analytics page", async ({ page }) => {
      await clickNavLink(page, "/analytics");
      await expect(page).toHaveURL(/\/analytics/);
    });

    test("navigates to Team page", async ({ page }) => {
      await clickNavLink(page, "/team");
      await expect(page).toHaveURL(/\/team/);
    });

    test("navigates to Settings page", async ({ page }) => {
      await clickNavLink(page, "/settings");
      await expect(page).toHaveURL(/\/settings\/?$/);
      await expect(page.getByRole("heading", { level: 1, name: /settings/i })).toBeVisible();
    });

    test("highlights active navigation item", async ({ page }) => {
      await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60000 });

      if (isDesktopLayout(page)) {
        const sidebar = page.locator("aside");
        await expectLinkActive(sidebar.locator('a[href="/"]'));
        await sidebar.locator('a[href="/papers"]').click();
        await expect(page).toHaveURL(/\/papers/);
        await expectLinkActive(sidebar.locator('a[href="/papers"]'));
        return;
      }

      const mobileNav = page.getByRole("navigation", { name: /primary mobile navigation/i });
      await expectLinkActive(mobileNav.locator('a[href="/"]'));
      await mobileNav.locator('a[href="/papers"]').click();
      await expect(page).toHaveURL(/\/papers/);
      await expectLinkActive(mobileNav.locator('a[href="/papers"]'));
    });

    test("can collapse and expand sidebar", async ({ page }) => {
      const collapseButton = page.getByRole("button", { name: /collapse sidebar/i });

      if (await collapseButton.isVisible()) {
        await collapseButton.click();

        const sidebar = page.locator("aside");
        await expect(sidebar).toHaveClass(/w-16/);

        await page.getByRole("button", { name: /expand sidebar/i }).click();
        await expect(sidebar).toHaveClass(/w-64/);
      }
    });
  });

  test.describe("Responsive Behavior", () => {
    test("hides sidebar on mobile viewport", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.locator("aside")).toBeHidden();
    });

    test("shows sidebar on desktop viewport", async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 800 });
      await expect(page.locator("aside")).toBeVisible();
    });
  });

  test.describe("Navbar", () => {
    test("displays user information or menu", async ({ page }) => {
      await expect(page.locator("header, nav").first()).toBeVisible();
    });
  });

  test.describe("Protected Routes", () => {
    test("redirects to login when accessing protected route while logged out", async ({
      browser,
    }) => {
      const context = await browser.newContext();
      const newPage = await context.newPage();

      await newPage.goto("/dashboard");
      await expect(newPage).toHaveURL(/\/login/);

      await newPage.goto("/papers");
      await expect(newPage).toHaveURL(/\/login/);

      await newPage.goto("/projects");
      await expect(newPage).toHaveURL(/\/login/);

      await context.close();
    });
  });

  test.describe("Dashboard Workflow CTAs", () => {
    test("Dashboard has workflow action links", async ({ page }) => {
      await page.goto("/");
      await expect(page.getByRole("heading", { level: 1, name: /welcome back/i })).toBeVisible();

      await expect(page.getByRole("button", { name: /search papers/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /view papers/i })).toBeVisible();
      await expect(page.getByRole("button", { name: /start transfer/i })).toBeVisible();
    });

    test("Workflow CTA navigates to Search page", async ({ page }) => {
      await page.goto("/");
      await expect(page.getByRole("heading", { level: 1, name: /welcome back/i })).toBeVisible();
      await page.getByRole("button", { name: /search papers/i }).click();
      await expect(page).toHaveURL(/\/search/);
    });

    test("Workflow CTA navigates to Papers page", async ({ page }) => {
      await page.goto("/");
      await expect(page.getByRole("heading", { level: 1, name: /welcome back/i })).toBeVisible();
      await page.getByRole("button", { name: /view papers/i }).click();
      await expect(page).toHaveURL(/\/papers/);
    });

    test("Workflow CTA navigates to Transfer page", async ({ page }) => {
      await page.goto("/");
      await expect(page.getByRole("heading", { level: 1, name: /welcome back/i })).toBeVisible();
      await page.getByRole("button", { name: /start transfer/i }).click();
      await expect(page).toHaveURL(/\/transfer/);
    });
  });
});
