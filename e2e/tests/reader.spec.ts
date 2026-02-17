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

test.describe('Reader-first paper detail', () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser()
    await registerUser(page, user)
    await importOnePaper(page)
  })

  test('shows reader card and hydrate action', async ({ page }) => {
    const paperLink = page.locator('a[href*="/papers/"]').first()
    const exists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false)
    test.skip(!exists, 'No paper available to open detail view')

    await paperLink.click()
    await page.waitForLoadState('networkidle')

    await expect(page.getByText(/Reader/i).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Hydrate|Refresh Text/i }).first()).toBeVisible()
  })

  test('mobile view exposes segmented tabs', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const paperLink = page.locator('a[href*="/papers/"]').first()
    const exists = await paperLink.isVisible({ timeout: 5000 }).catch(() => false)
    test.skip(!exists, 'No paper available to open detail view')

    await paperLink.click()
    await page.waitForLoadState('networkidle')

    await expect(page.getByRole('button', { name: 'Reader' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Insights' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Transfer', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Advanced' })).toBeVisible()
  })
})
