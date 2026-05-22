import { test, expect } from '@playwright/test'

const TEST_USER = `testuser_${Date.now()}`
const TEST_EMAIL = `test_${Date.now()}@example.com`
const TEST_PASSWORD = 'testpass123'

test.describe('Admin UI visibility', () => {
  test('regular user cannot see blog management buttons', async ({ page }) => {
    // Register
    await page.goto('/register')
    await page.fill('input[type="text"]', TEST_USER)
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.fill('input[type="password"]', TEST_PASSWORD)
    await page.fill('input[type="password"]', TEST_PASSWORD)
    // The register form has 4 password inputs? No, let's check structure
    // Actually there are 4 inputs: username, email, password, confirm password
    const inputs = page.locator('input[type="password"]')
    await inputs.nth(0).fill(TEST_PASSWORD)
    await inputs.nth(1).fill(TEST_PASSWORD)
    await page.click('button:has-text("注册")')
    await page.waitForTimeout(1000)

    // Should redirect to login after success, or auto login
    // Wait for navigation
    await page.waitForURL(/.*login|.*/, { timeout: 5000 })

    // Login
    await page.goto('/login')
    await page.fill('input[type="text"]', TEST_USER)
    const passwordInput = page.locator('input[type="password"]')
    await passwordInput.fill(TEST_PASSWORD)
    await page.click('button:has-text("登录")')
    await page.waitForTimeout(1500)

    // Navigate to blogs
    await page.goto('/blogs')
    await page.waitForTimeout(1000)

    // Regular user should NOT see "新建文章" button
    const createBtn = page.locator('text=新建文章')
    await expect(createBtn).toHaveCount(0)

    // Navigate to forums
    await page.goto('/forums')
    await page.waitForTimeout(1000)

    // Regular user should NOT see "新建分区" button
    const createZoneBtn = page.locator('text=新建分区')
    await expect(createZoneBtn).toHaveCount(0)
  })
})
