import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AgentTraceDetailPage from './AgentTraceDetailPage'
import type { AgentSpan, AgentTrace } from '../../types/agentMonitoring'

const getAgentTraceMock = vi.fn()
const getAgentTraceSpansMock = vi.fn()
const getTraceEvaluationsMock = vi.fn()

vi.mock('../../api/agentMonitoring', () => ({
  getAgentTrace: (...args: unknown[]) => getAgentTraceMock(...args),
  getAgentTraceSpans: (...args: unknown[]) => getAgentTraceSpansMock(...args),
  getTraceEvaluations: (...args: unknown[]) => getTraceEvaluationsMock(...args),
}))

const baseTrace: AgentTrace = {
  id: 1,
  trace_id: 'agent-test',
  conversation_id: 10,
  user_id: 1,
  graph_name: 'chat_agent',
  status: 'completed',
  input_message: '搜索 Python 新闻',
  output_message: '根据联网搜索结果...',
  total_tokens: 100,
  prompt_tokens: 60,
  completion_tokens: 40,
  tool_calls_count: 1,
  node_steps: 3,
  latency_ms: 1200,
  started_at: '2026-06-02T12:00:00Z',
  ended_at: '2026-06-02T12:00:01Z',
  error_type: null,
  error_message: null,
  is_flagged: false,
  meta: null,
}

function makeSpan(overrides: Partial<AgentSpan>): AgentSpan {
  return {
    id: 1,
    trace_id: 'agent-test',
    parent_span_id: null,
    span_type: 'node',
    span_name: 'agent',
    status: 'completed',
    started_at: '2026-06-02T12:00:00Z',
    ended_at: '2026-06-02T12:00:01Z',
    latency_ms: 100,
    input_data: null,
    output_data: null,
    error_info: null,
    token_usage: null,
    meta: null,
    ...overrides,
  }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/admin/agent-monitoring/agent-test']}>
      <Routes>
        <Route path="/admin/agent-monitoring/:traceId" element={<AgentTraceDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('AgentTraceDetailPage span tree', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getAgentTraceMock.mockResolvedValue({ data: baseTrace })
    getTraceEvaluationsMock.mockResolvedValue({ data: { items: [], total: 0 } })
  })

  it('按父子关系展示联网搜索内部流程和 metadata', async () => {
    getAgentTraceSpansMock.mockResolvedValue({
      data: {
        items: [
          makeSpan({ id: 1, span_type: 'tool', span_name: 'search_web' }),
          makeSpan({
            id: 2,
            parent_span_id: 1,
            span_type: 'web_search',
            span_name: 'query_expansion',
            output_data: { queries: ['q1', 'q2', 'q3'], query_count: 3, fallback: false },
          }),
          makeSpan({
            id: 3,
            parent_span_id: 1,
            span_type: 'web_search',
            span_name: 'iqs_search_batch',
            output_data: { query_count: 3, parallel: true, raw_count: 3, failed_count: 0 },
            meta: { provider: 'iqs' },
          }),
          makeSpan({
            id: 4,
            parent_span_id: 3,
            span_type: 'web_search',
            span_name: 'iqs_search_single',
            input_data: { query: 'q1' },
            output_data: { result_count: 1 },
          }),
        ],
      },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getAllByText('联网搜索')).toHaveLength(3)
    })
    expect(screen.getByText('iqs_search_batch')).toBeInTheDocument()
    expect(screen.getByText('3 queries · parallel · 3 raw · 0 failed')).toBeInTheDocument()

    await userEvent.click(screen.getByText('iqs_search_batch'))
    expect(await screen.findByText(/"provider": "iqs"/)).toBeInTheDocument()
  })

  it('兼容没有 parent_span_id 的旧平铺 span', async () => {
    getAgentTraceSpansMock.mockResolvedValue({
      data: {
        items: [
          makeSpan({ id: 1, span_type: 'llm', span_name: 'deepseek-chat' }),
          makeSpan({ id: 2, span_type: 'tool', span_name: 'search_web' }),
        ],
      },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('deepseek-chat')).toBeInTheDocument()
    })
    expect(screen.getByText('search_web')).toBeInTheDocument()
  })
})
