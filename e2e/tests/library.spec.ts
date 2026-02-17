import { test, expect, registerUser, generateTestUser } from './fixtures'

test.describe('Library V2 - Papers list surface', () => {
  test.beforeEach(async ({ page }) => {
    const user = generateTestUser()
    await registerUser(page, user)
    await page.goto('/papers')
    await page.waitForLoadState('networkidle')
  })

  test('shows quick export actions for open formats', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'RIS' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'CSL-JSON' })).toBeVisible()
  })

  test('keeps import flow accessible', async ({ page }) => {
    await page.getByRole('button', { name: /import papers/i }).last().click()
    await expect(page.getByText(/DOI/i).first()).toBeVisible()
  })
})
