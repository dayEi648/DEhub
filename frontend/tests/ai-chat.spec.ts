import { expect, test } from '@playwright/test'

interface CapturedChatRequest {
  conversationId?: number
  userInput: string
}

test.describe('AI chat page', () => {
  test('loads conversations and sends messages with mocked API', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-token')
      localStorage.setItem(
        'user',
        JSON.stringify({
          id: 1001,
          username: 'tester',
          permission: 0,
          created_at: '2026-01-01T00:00:00',
        }),
      )
    })

    const now = '2026-05-22T09:00:00'
    const capturedRequests: CapturedChatRequest[] = []
    const capturedIncludeHiddenValues: string[] = []
    const conversations = [
      {
        id: 1,
        title: '旧对话',
        created_at: now,
        updated_at: now,
        last_message_at: now,
      },
    ]
    const messageStore = new Map<number, Array<Record<string, unknown>>>([
      [
        1,
        [
          {
            id: 1,
            conversation_id: 1,
            role: 'user',
            content: '你好',
            meta: null,
            created_at: now,
          },
          {
            id: 2,
            conversation_id: 1,
            role: 'assistant',
            content: '你好，我是 AI 助手。',
            meta: null,
            created_at: '2026-05-22T09:00:01',
          },
          {
            id: 3,
            conversation_id: 1,
            role: 'assistant',
            content: '好的，我帮你联网搜索一下。',
            meta: { tool_calls: [{ name: 'web_search' }] },
            created_at: '2026-05-22T09:00:02',
          },
          {
            id: 4,
            conversation_id: 1,
            role: 'tool',
            content: '工具返回的原始搜索结果',
            meta: { tool_name: 'web_search' },
            created_at: '2026-05-22T09:00:03',
          },
          {
            id: 5,
            conversation_id: 1,
            role: 'assistant',
            content: '根据联网搜索结果，我整理如下。',
            meta: null,
            created_at: '2026-05-22T09:00:04',
          },
        ],
      ],
    ])

    await page.route('**/api/v1/ai_chat/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const pathname = url.pathname
      const method = request.method()

      const replyJson = async (status: number, payload: unknown) =>
        route.fulfill({
          status,
          contentType: 'application/json',
          body: JSON.stringify(payload),
        })

      if (method === 'GET' && pathname === '/api/v1/ai_chat/conversations') {
        return replyJson(200, { items: conversations, total: conversations.length })
      }

      const messageMatch = pathname.match(/^\/api\/v1\/ai_chat\/conversations\/(\d+)\/messages$/)
      if (method === 'GET' && messageMatch) {
        capturedIncludeHiddenValues.push(url.searchParams.get('include_hidden') ?? '')
        const conversationId = Number(messageMatch[1])
        return replyJson(200, messageStore.get(conversationId) ?? [])
      }

      if (method === 'POST' && pathname === '/api/v1/ai_chat/chat') {
        const body = request.postDataJSON() as {
          conversation_id?: number
          user_input: string
        }
        capturedRequests.push({
          conversationId: body.conversation_id,
          userInput: body.user_input,
        })

        const conversationId = body.conversation_id ?? 2
        if (!body.conversation_id) {
          conversations.unshift({
            id: 2,
            title: '自动生成标题 2',
            created_at: '2026-05-22T10:00:00',
            updated_at: '2026-05-22T10:00:00',
            last_message_at: '2026-05-22T10:00:00',
          })
        }
        const currentMessages = messageStore.get(conversationId) ?? []
        const nextId = currentMessages.length + 1
        const createdAt = body.conversation_id ? '2026-05-22T09:02:00' : '2026-05-22T10:00:00'
        messageStore.set(conversationId, [
          ...currentMessages,
          {
            id: nextId,
            conversation_id: conversationId,
            role: 'user',
            content: body.user_input,
            meta: null,
            created_at: createdAt,
          },
          {
            id: nextId + 1,
            conversation_id: conversationId,
            role: 'assistant',
            content: body.conversation_id ? '这是 AI 回复' : '这是新会话回复',
            meta: null,
            created_at: createdAt,
          },
        ])

        return replyJson(200, {
          response: body.conversation_id ? '这是 AI 回复' : '这是新会话回复',
          conversation_id: conversationId,
        })
      }

      const deleteMatch = pathname.match(/^\/api\/v1\/ai_chat\/conversations\/(\d+)$/)
      if (method === 'DELETE' && deleteMatch) {
        const conversationId = Number(deleteMatch[1])
        const index = conversations.findIndex((item) => item.id === conversationId)
        if (index >= 0) {
          conversations.splice(index, 1)
        }
        messageStore.delete(conversationId)
        return route.fulfill({ status: 204, body: '' })
      }

      return route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ message: `Unhandled route: ${method} ${pathname}` }),
      })
    })

    await page.goto('/ai-chat')

    await expect(page.locator('h1:has-text("AI 对话实验室")')).toBeVisible()
    await expect(page.locator('text=旧对话')).toBeVisible()
    await expect(page.locator('text=你好，我是 AI 助手。')).toBeVisible()
    await expect(page.locator('text=好的，我帮你联网搜索一下。')).toBeVisible()
    await expect(page.locator('text=根据联网搜索结果，我整理如下。')).toBeVisible()
    await expect(page.locator('text=工具返回的原始搜索结果')).toHaveCount(0)
    await expect(page.locator('label:has-text("包含隐藏消息")')).toHaveCount(0)
    expect(capturedIncludeHiddenValues).toContain('false')

    await page.fill('[data-testid="ai-chat-input"]', '请总结这次改动')
    await page.click('[data-testid="ai-chat-send"]')

    await expect(page.locator('text=这是 AI 回复')).toBeVisible()
    expect(capturedRequests[0]).toEqual({
      conversationId: 1,
      userInput: '请总结这次改动',
    })

    await page.click('button:has-text("新建对话")')
    await page.fill('[data-testid="ai-chat-input"]', '新会话提问')
    await page.click('[data-testid="ai-chat-send"]')

    await expect(page.locator('text=这是新会话回复')).toBeVisible()
    expect(capturedRequests[1]).toEqual({
      conversationId: undefined,
      userInput: '新会话提问',
    })
  })
})
