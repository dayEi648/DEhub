import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import OpenAPIKnowledgePage from './OpenAPIKnowledgePage'

const getUserMock = vi.fn()

const uploadOpenAPIDocumentMock = vi.fn()
const getOpenAPIDocumentsMock = vi.fn()
const getOpenAPIEndpointsMock = vi.fn()
const getOpenAPIDocumentMock = vi.fn()
const searchOpenAPIKnowledgeMock = vi.fn()
const deleteOpenAPIEndpointMock = vi.fn()

vi.mock('../../utils/auth', () => ({
  getUser: () => getUserMock(),
}))

vi.mock('../../api/openapiKnowledge', () => ({
  uploadOpenAPIDocument: (...args: unknown[]) => uploadOpenAPIDocumentMock(...args),
  getOpenAPIDocuments: (...args: unknown[]) => getOpenAPIDocumentsMock(...args),
  getOpenAPIEndpoints: (...args: unknown[]) => getOpenAPIEndpointsMock(...args),
  getOpenAPIDocument: (...args: unknown[]) => getOpenAPIDocumentMock(...args),
  searchOpenAPIKnowledge: (...args: unknown[]) => searchOpenAPIKnowledgeMock(...args),
  deleteOpenAPIDocument: vi.fn(),
  deleteOpenAPIEndpoint: (...args: unknown[]) => deleteOpenAPIEndpointMock(...args),
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
    message: vi.fn(),
  },
}))

function adminUser() {
  return {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    permission: 1,
  }
}

describe('OpenAPIKnowledgePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getOpenAPIDocumentsMock.mockResolvedValue({ data: { items: [], total: 0 } })
    getOpenAPIEndpointsMock.mockResolvedValue({ data: { items: [], total: 0 } })
    searchOpenAPIKnowledgeMock.mockResolvedValue({ data: { items: [], total: 0 } })
    getOpenAPIDocumentMock.mockResolvedValue({
      data: {
        id: 99,
        filename: 'petstore.json',
        status: 'processing',
        endpoint_count: 0,
        chunk_count: 0,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    })
    uploadOpenAPIDocumentMock.mockResolvedValue({
      data: {
        document_id: 99,
        filename: 'petstore.json',
        status: 'pending',
      },
    })
    deleteOpenAPIEndpointMock.mockResolvedValue(undefined)
  })

  it('非管理员不应暴露 OpenAPI 知识库字样', () => {
    getUserMock.mockReturnValue({
      id: 2,
      username: 'user',
      email: 'user@example.com',
      permission: 0,
    })

    render(<OpenAPIKnowledgePage />)

    expect(screen.getByText('权限不足')).toBeInTheDocument()
    expect(screen.queryByText(/OpenAPI|知识库管理页面/i)).not.toBeInTheDocument()
  })

  it('初始进入页面不应显示“未找到相关接口”', async () => {
    getUserMock.mockReturnValue(adminUser())

    render(<OpenAPIKnowledgePage />)

    await waitFor(() => {
      expect(getOpenAPIDocumentsMock).toHaveBeenCalled()
      expect(getOpenAPIEndpointsMock).toHaveBeenCalled()
    })

    expect(screen.queryByText('当前知识库未找到相关接口')).not.toBeInTheDocument()
  })

  it('空列表分页应显示 0 / 0', async () => {
    getUserMock.mockReturnValue(adminUser())

    render(<OpenAPIKnowledgePage />)

    await waitFor(() => {
      expect(getOpenAPIDocumentsMock).toHaveBeenCalled()
    })

    expect(screen.getAllByText('0 / 0')).toHaveLength(2)
  })

  it('上传成功后应使用 skip=0 刷新，并清空检索结果与文件输入值', async () => {
    getUserMock.mockReturnValue(adminUser())

    getOpenAPIDocumentsMock
      .mockResolvedValueOnce({
        data: {
          items: [
            {
              id: 88,
              filename: 'doc-old.json',
              status: 'completed',
              endpoint_count: 1,
              chunk_count: 1,
              error_message: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          total: 1,
        },
      })
      .mockResolvedValue({ data: { items: [], total: 0 } })

    getOpenAPIEndpointsMock.mockResolvedValue({ data: { items: [], total: 0 } })

    searchOpenAPIKnowledgeMock.mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            document_id: 1,
            chunk_id: 'chunk-1',
            method: 'GET',
            path: '/pets',
            summary: 'list pets',
            description: '',
            tags: ['pet'],
            operation_id: 'listPets',
            content: 'GET /pets',
            similarity_score: 0.92,
          },
        ],
        total: 1,
      },
    })

    render(<OpenAPIKnowledgePage />)

    await waitFor(() => {
      expect(getOpenAPIDocumentsMock).toHaveBeenCalled()
    })

    fireEvent.change(screen.getByPlaceholderText('输入接口问题或关键词'), {
      target: { value: 'pet list' },
    })
    fireEvent.click(screen.getByRole('button', { name: '检索' }))

    await waitFor(() => {
      expect(screen.getByText('/pets')).toBeInTheDocument()
    })

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['{"openapi":"3.0.0"}'], 'petstore.json', { type: 'application/json' })
    fireEvent.change(fileInput, { target: { files: [file] } })

    fireEvent.click(screen.getByRole('button', { name: '上传并解析' }))

    await waitFor(() => {
      expect(uploadOpenAPIDocumentMock).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(getOpenAPIDocumentsMock).toHaveBeenLastCalledWith(expect.objectContaining({ skip: 0 }))
    })

    expect(screen.queryByText('/pets')).not.toBeInTheDocument()
    expect(fileInput.value).toBe('')
  })

  it('轮询在慢请求时不应并发触发新请求', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      getUserMock.mockReturnValue(adminUser())
      getOpenAPIDocumentMock.mockImplementation(() => new Promise(() => {}))

      render(<OpenAPIKnowledgePage />)

      await waitFor(() => {
        expect(getOpenAPIDocumentsMock).toHaveBeenCalled()
      })

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const file = new File(['{"openapi":"3.0.0"}'], 'petstore.json', { type: 'application/json' })
      fireEvent.change(fileInput, { target: { files: [file] } })
      fireEvent.click(screen.getByRole('button', { name: '上传并解析' }))

      await waitFor(() => {
        expect(uploadOpenAPIDocumentMock).toHaveBeenCalled()
      })
      await waitFor(() => {
        expect(getOpenAPIDocumentMock).toHaveBeenCalledTimes(1)
      })

      await vi.advanceTimersByTimeAsync(8000)
      expect(getOpenAPIDocumentMock).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

  it('删除端点返回 404 时按已删除处理并刷新列表', async () => {
    getUserMock.mockReturnValue(adminUser())
    const endpoint = {
      id: 7,
      document_id: 1,
      chunk_id: 'chunk-7',
      method: 'GET',
      path: '/pets',
      summary: 'list pets',
      description: '',
      tags: ['pet'],
      operation_id: 'listPets',
      content: 'GET /pets',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    getOpenAPIEndpointsMock.mockResolvedValue({
      data: {
        items: [endpoint],
        total: 1,
      },
    })
    deleteOpenAPIEndpointMock.mockRejectedValue({
      isAxiosError: true,
      response: {
        status: 404,
        data: {
          code: 404,
          message: '端点不存在',
        },
      },
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<OpenAPIKnowledgePage />)

    await waitFor(() => {
      expect(screen.getByText('/pets')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: '删除' }))

    await waitFor(() => {
      expect(deleteOpenAPIEndpointMock).toHaveBeenCalledWith(7)
    })
    await waitFor(() => {
      expect(getOpenAPIEndpointsMock).toHaveBeenCalledTimes(2)
    })
  })
})
