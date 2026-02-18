import { test, expect, registerUser, generateTestUser } from './fixtures'

async function importOnePaper(page: import('@playwright/test').Page) {
  await page.goto('/papers')
  await page.waitForLoadState('domcontentloaded')
  await page.getByRole('button', { name: /import papers/i }).last().click()
  await page.fill('#doi', '10.1038/nature12373')
  await page.getByRole('button', { name: 'Import', exact: true }).click()

  await expect
    .poll(
      async () => {
        const papersPagePath = new URL(page.url()).pathname
        if (!/\/papers\/?$/.test(papersPagePath)) {
          return 0
        }
        return await page.locator('main a[href^="/papers/"]:not([href="/papers"])').count()
      },
      { timeout: 30000 }
    )
    .toBeGreaterThan(0)

  await page.goto('/papers')
  await page.waitForLoadState('domcontentloaded')
}

test.describe('Zotero transfer surface', () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser()
    await registerUser(page, user)
    await importOnePaper(page)
  })

  test('shows transfer hub with Zotero sync action', async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first()
    const exists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false)
    test.skip(!exists, 'No paper available to open detail view')

    await paperLink.click()
    await page.waitForLoadState('networkidle')

    const transferTab = page.getByRole('button', { name: /^transfer$/i }).first()
    if (await transferTab.isVisible().catch(() => false)) {
      await transferTab.click()
    }

    await expect
      .poll(async () => {
        const transferHubVisible = await page
          .getByRole('heading', { name: /Transfer Hub|Transfer-Hub/i })
          .first()
          .isVisible()
          .catch(() => false)
        const syncVisible = await page
          .getByRole('button', { name: /Sync to Zotero|Mit Zotero synchronisieren/i })
          .first()
          .isVisible()
          .catch(() => false)
        return transferHubVisible || syncVisible
      })
      .toBe(true)

    const syncButton = page.getByRole('button', { name: /Sync to Zotero|Mit Zotero synchronisieren/i }).first()
    await expect(syncButton).toBeVisible()
  })
})
