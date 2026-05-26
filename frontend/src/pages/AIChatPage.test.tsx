import { MemoryRouter } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, beforeAll } from 'vitest'
import AIChatPage from './AIChatPage'

const getUserMock = vi.fn()

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
  })

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
})
