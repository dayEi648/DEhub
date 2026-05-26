import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { uploadOpenAPIDocument } from './openapiKnowledge'
import request from '../utils/request'

describe('openapiKnowledge api', () => {
  const originalAdapter = request.defaults.adapter

  afterEach(() => {
    request.defaults.adapter = originalAdapter
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('上传 OpenAPI 文档时保持 FormData 请求体', async () => {
    const captured: { config?: InternalAxiosRequestConfig } = {}
    const adapter: AxiosAdapter = async (config) => {
      captured.config = config
      return {
        data: {
          document_id: 1,
          filename: 'openapi.json',
          status: 'pending',
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
        request: {},
      } satisfies AxiosResponse
    }

    request.defaults.adapter = adapter

    await uploadOpenAPIDocument(
      new File(['{"openapi":"3.0.0"}'], 'openapi.json', { type: 'application/json' }),
    )

    const capturedConfig = captured.config
    expect(capturedConfig).toBeDefined()
    expect(capturedConfig?.data).toBeInstanceOf(FormData)
    expect(capturedConfig?.headers.getContentType()).not.toBe('application/json')
  })
})
