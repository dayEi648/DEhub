import { test, expect } from '@playwright/test'

test.describe('Basic page rendering', () => {
  test('login page renders without alert', async ({ page }) => {
    const dialogs: string[] = []
    page.on('dialog', (dialog) => {
      dialogs.push(dialog.message())
      dialog.dismiss()
    })

    await page.goto('/login')
    await expect(page.locator('text=欢迎回来')).toBeVisible()

    // Click login with empty fields to trigger validation toast (not alert)
    await page.click('button:has-text("登录")')
    await page.waitForTimeout(500)

    expect(dialogs).toHaveLength(0)
  })

  test('register page renders without alert', async ({ page }) => {
    const dialogs: string[] = []
    page.on('dialog', (dialog) => {
      dialogs.push(dialog.message())
      dialog.dismiss()
    })

    await page.goto('/register')
    await expect(page.locator('text=创建账号')).toBeVisible()

    // Click register with empty fields to trigger validation toast (not alert)
    await page.click('button:has-text("注册")')
    await page.waitForTimeout(500)

    expect(dialogs).toHaveLength(0)
  })

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto('/blogs')
    await expect(page).toHaveURL(/.*login/)
  })
})
