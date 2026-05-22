import { test } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SCREENSHOT_DIR = path.join(__dirname, '..', 'test-screenshots')

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
}

test('screenshot login page', async ({ page }) => {
  await page.goto('/login')
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'login.png'), fullPage: true })
})

test('screenshot register page', async ({ page }) => {
  await page.goto('/register')
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'register.png'), fullPage: true })
})

test('screenshot blogs page (redirects to login)', async ({ page }) => {
  await page.goto('/blogs')
  await page.waitForURL(/.*login/)
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'blogs-unauth.png'), fullPage: true })
})
