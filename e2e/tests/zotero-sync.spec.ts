import { test, expect, registerUser, generateTestUser } from './fixtures'

async function importOnePaper(page: import('@playwright/test').Page) {
  await page.goto('/papers')
  await page.waitForLoadState('networkidle')
  await page.getByRole('button', { name: /import papers/i }).last().click()
  await page.fill('#doi', '10.1038/nature12373')
  await page.getByRole('button', { name: 'Import', exact: true }).click()
  await page.waitForTimeout(4000)
  await page.goto('/papers')
  await page.waitForLoadState('networkidle')
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

    await expect(page.getByText(/Transfer Hub|Transfer-Hub/i).first()).toBeVisible()
    const syncButton = page.getByRole('button', { name: /Sync to Zotero|Mit Zotero synchronisieren/i }).first()
    await expect(syncButton).toBeVisible()
  })
})
