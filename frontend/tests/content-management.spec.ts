import { expect, test } from '@playwright/test'

function mockUser(permission: 0 | 1 | 2) {
  return {
    id: permission + 1,
    username: permission === 2 ? 'super_admin' : permission === 1 ? 'admin' : 'member',
    email: 'user@example.com',
    created_at: '2026-05-22T00:00:00Z',
    permission,
    is_deleted: false,
    avatar_url: null,
    personal_profile: null,
  }
}

async function setAuth(page: import('@playwright/test').Page, permission: 0 | 1 | 2) {
  await page.addInitScript((user) => {
    window.localStorage.setItem('token', 'test-token')
    window.localStorage.setItem('user', JSON.stringify(user))
  }, mockUser(permission))
}

test.describe('content management affordances', () => {
  test('super admin can create blog category and generate summary', async ({ page }) => {
    await setAuth(page, 2)

    await page.route(/\/api\/v1\/blog_posts(\/|\?|$)/, async (route) => {
      const request = route.request()
      if (request.method() === 'POST' && request.url().includes('/generate-summary')) {
        expect(typeof request.postDataJSON().content_md).toBe('string')
        await route.fulfill({ json: { summary: '这是一段由轻量 AI 生成的文章摘要。' } })
        return
      }
      await route.fulfill({ json: { items: [], total: 0 } })
    })
    await page.route(/\/api\/v1\/blog_categories(\/|\?|$)/, async (route) => {
      const request = route.request()
      if (request.method() === 'POST') {
        expect(request.postDataJSON()).toMatchObject({ name: '工程实践' })
        await route.fulfill({
          json: { id: 2, name: '工程实践', slug: 'engineering', description: '', post_count: 0 },
        })
        return
      }
      await route.fulfill({
        json: [{ id: 1, name: '默认分类', slug: 'default', description: null, post_count: 0 }],
      })
    })

    await page.goto('/blogs')
    await expect(page.getByRole('button', { name: '创建分类' })).toBeVisible()

    await page.getByRole('button', { name: '创建分类' }).click()
    await page.getByPlaceholder('例如：工程实践').fill('工程实践')
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await expect(page.getByRole('heading', { name: '创建博客分类' })).toHaveCount(0)

    await page.getByRole('button', { name: '新建文章' }).click()
    await page.getByPlaceholder('文章标题', { exact: true }).fill('测试文章')
    await page.getByPlaceholder('支持 Markdown 格式').fill('这是一段用于触发摘要生成的正文。'.repeat(12))
    await page.getByRole('button', { name: '轻量 AI 生成' }).click()

    await expect(page.getByPlaceholder('文章摘要')).toHaveValue('这是一段由轻量 AI 生成的文章摘要。')
  })

  test('forum zone manager is selected through username search', async ({ page }) => {
    await setAuth(page, 1)

    await page.route('**/api/v1/forum_zones/**', async (route) => {
      const request = route.request()
      if (request.method() === 'POST') {
        expect(request.postDataJSON()).toMatchObject({
          zone_name: 'AI 讨论',
          manager_id: 7,
        })
        await route.fulfill({
          json: {
            id: 1,
            slug: 'ai',
            zone_name: 'AI 讨论',
            description: '',
            manager_id: 7,
            manager: { id: 7, username: 'alice', avatar_url: null },
            view_count: 0,
            created_at: '2026-05-22T00:00:00Z',
          },
        })
        return
      }
      await route.fulfill({ json: [] })
    })
    await page.route('**/api/v1/users/**', async (route) => {
      const url = new URL(route.request().url())
      expect(url.searchParams.get('username')).toContain('ali')
      await route.fulfill({
        json: {
          items: [
            {
              id: 7,
              username: 'alice',
              email: 'alice@example.com',
              created_at: '2026-05-22T00:00:00Z',
              permission: 0,
              is_deleted: false,
              avatar_url: null,
              personal_profile: null,
            },
          ],
          total: 1,
        },
      })
    })

    await page.goto('/forums')
    await expect(page.getByRole('button', { name: '新建分区' })).toBeVisible()
    await page.getByRole('button', { name: '新建分区' }).click()
    await page.getByPlaceholder('分区名称').fill('AI 讨论')
    await page.getByPlaceholder('输入用户名搜索；留空默认当前用户').fill('ali')
    await page.getByRole('button', { name: /alice/ }).click()
    await page.getByRole('button', { name: '保存' }).click()
  })
})
