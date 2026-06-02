import { MemoryRouter } from 'react-router-dom'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, beforeAll } from 'vitest'
import type { AxiosResponse } from 'axios'
import AIChatPage from './AIChatPage'
import { chatWithAI, getConversationList, getConversationMessages } from '../api/aiChat'

const getUserMock = vi.fn()

function mockAxiosResponse<T>(data: T): AxiosResponse<T> {
  return { data } as AxiosResponse<T>
}

vi.mock('../utils/auth', () => ({
  getUser: () => getUserMock(),
}))

vi.mock('../hooks/useLogout', () => ({
  useLogout: () => vi.fn(),
}))

vi.mock('../components/AppTopNav', () => ({
  default: () => <div data-testid="top-nav">top-nav</div>,
}))

vi.mock('../components/Footer', () => ({
  default: () => <div data-testid="footer">footer</div>,
}))

vi.mock('../api/aiChat', () => ({
  chatWithAI: vi.fn(),
  deleteConversation: vi.fn(),
  getConversationMessages: vi.fn(),
  getConversationList: vi.fn().mockResolvedValue({
    data: {
      items: [],
      total: 0,
    },
  }),
}))

describe('AIChatPage OpenAPI 入口可见性', () => {
  beforeAll(() => {
    Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
      value: vi.fn(),
      writable: true,
    })
  })

  beforeEach(() => {
    vi.clearAllMocks()
    getConversationListMock.mockResolvedValue(
      mockAxiosResponse({
        items: [],
        total: 0,
      }),
    )
    getConversationMessagesMock.mockResolvedValue(mockAxiosResponse([]))
  })

  const chatWithAIMock = vi.mocked(chatWithAI)
  const getConversationListMock = vi.mocked(getConversationList)
  const getConversationMessagesMock = vi.mocked(getConversationMessages)

  it('管理员可以看到知识库入口', async () => {
    getUserMock.mockReturnValue({
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      permission: 1,
    })

    render(
      <MemoryRouter>
        <AIChatPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: '接口知识库' })).toBeInTheDocument()
    })
  })

  it('普通用户看不到知识库入口', async () => {
    getUserMock.mockReturnValue({
      id: 2,
      username: 'user',
      email: 'user@example.com',
      permission: 0,
    })

    render(
      <MemoryRouter>
        <AIChatPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: '接口知识库' })).not.toBeInTheDocument()
    })
  })

  it('发送后消息列表短暂滞后时仍显示 POST 返回的 AI 回复', async () => {
    getUserMock.mockReturnValue({
      id: 2,
      username: 'user',
      email: 'user@example.com',
      permission: 0,
    })

    getConversationListMock.mockResolvedValue(
      mockAxiosResponse({
        items: [
          {
            id: 1,
            title: '旧对话',
            created_at: '2026-06-02T10:00:00',
            updated_at: '2026-06-02T10:00:00',
            last_message_at: '2026-06-02T10:00:00',
          },
        ],
        total: 1,
      }),
    )
    getConversationMessagesMock.mockResolvedValue(
      mockAxiosResponse([
        {
          id: 1,
          conversation_id: 1,
          role: 'user',
          content: '你好',
          meta: null,
          created_at: '2026-06-02T10:00:00',
        },
        {
          id: 2,
          conversation_id: 1,
          role: 'assistant',
          content: '你好，我是 AI 助手。',
          meta: null,
          created_at: '2026-06-02T10:00:01',
        },
      ]),
    )
    chatWithAIMock.mockResolvedValue(
      mockAxiosResponse({
        conversation_id: 1,
        response: '根据联网搜索结果，我整理如下。',
      }),
    )

    render(
      <MemoryRouter>
        <AIChatPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('你好，我是 AI 助手。')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByTestId('ai-chat-input'), {
      target: { value: '帮我联网搜索 Python 最新信息' },
    })
    fireEvent.click(screen.getByTestId('ai-chat-send'))

    await waitFor(() => {
      expect(screen.getByText('根据联网搜索结果，我整理如下。')).toBeInTheDocument()
    })
    expect(getConversationMessagesMock).toHaveBeenCalledTimes(1)
  })
})
