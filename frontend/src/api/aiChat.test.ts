import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it } from 'vitest'
import { chatWithAI } from './aiChat'
import request from '../utils/request'

describe('aiChat api', () => {
  const originalAdapter = request.defaults.adapter

  afterEach(() => {
    request.defaults.adapter = originalAdapter
  })

  it('AI 对话请求应放宽超时时间，避免联网搜索被 30 秒截断', async () => {
    const captured: { config?: InternalAxiosRequestConfig } = {}
    const adapter: AxiosAdapter = async (config) => {
      captured.config = config
      return {
        data: {
          response: 'ok',
          conversation_id: 1,
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
        request: {},
      } satisfies AxiosResponse
    }

    request.defaults.adapter = adapter

    await chatWithAI({
      conversation_id: 1,
      user_input: '帮我联网搜索 Python 最新消息',
    })

    expect(captured.config?.timeout).toBe(180_000)
  })
})
