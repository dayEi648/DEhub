import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Bot,
  Wrench,
  BrainCircuit,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  User,
  Search,
} from 'lucide-react'
import { getAgentTrace, getAgentTraceSpans, getTraceEvaluations } from '../../api/agentMonitoring'
import type { AgentTrace, AgentSpan, AgentEvaluation } from '../../types/agentMonitoring'

const SPAN_TYPE_ICONS: Record<string, React.ReactNode> = {
  node: <Bot size={16} />,
  llm: <BrainCircuit size={16} />,
  tool: <Wrench size={16} />,
  compact: <Clock size={16} />,
  goal_gen: <BrainCircuit size={16} />,
  profile_update: <User size={16} />,
  title_gen: <Bot size={16} />,
  web_search: <Search size={16} />,
}

const SPAN_TYPE_LABELS: Record<string, string> = {
  node: '节点执行',
  llm: 'LLM 调用',
  tool: '工具调用',
  compact: '上下文压缩',
  goal_gen: '目标生成',
  profile_update: '画像更新',
  title_gen: '标题生成',
  web_search: '联网搜索',
}

const SPAN_TYPE_COLORS: Record<string, string> = {
  node: 'var(--color-accent-teal)',
  llm: 'var(--color-primary)',
  tool: 'var(--color-accent-amber)',
  compact: 'var(--color-muted-soft)',
  goal_gen: 'var(--color-muted-soft)',
  profile_update: 'var(--color-muted-soft)',
  title_gen: 'var(--color-muted-soft)',
  web_search: 'var(--color-accent-teal)',
}

interface SpanTreeNode extends AgentSpan {
  children: SpanTreeNode[]
}

function buildSpanTree(spans: AgentSpan[]): { roots: SpanTreeNode[]; hasHierarchy: boolean } {
  const nodes = new Map<number, SpanTreeNode>()
  spans.forEach((span) => {
    nodes.set(span.id, { ...span, children: [] })
  })

  let hasHierarchy = false
  const roots: SpanTreeNode[] = []
  spans.forEach((span) => {
    const node = nodes.get(span.id)!
    if (span.parent_span_id && nodes.has(span.parent_span_id)) {
      nodes.get(span.parent_span_id)!.children.push(node)
      hasHierarchy = true
    } else {
      roots.push(node)
    }
  })

  return { roots, hasHierarchy }
}

function formatWebSearchSummary(span: AgentSpan): string | null {
  if (span.span_type !== 'web_search') return null
  const data = span.output_data || span.meta || {}
  const queryCount = data.query_count
  const rawCount = data.raw_count
  const failedCount = data.failed_count
  const parallel = data.parallel

  const parts: string[] = []
  if (typeof queryCount === 'number') parts.push(`${queryCount} queries`)
  if (parallel === true) parts.push('parallel')
  if (typeof rawCount === 'number') parts.push(`${rawCount} raw`)
  if (typeof failedCount === 'number') parts.push(`${failedCount} failed`)
  return parts.length > 0 ? parts.join(' · ') : null
}

function formatDuration(ms: number | null): string {
  if (ms === null || ms === undefined) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

export default function AgentTraceDetailPage() {
  const navigate = useNavigate()
  const { traceId } = useParams<{ traceId: string }>()
  const [trace, setTrace] = useState<AgentTrace | null>(null)
  const [spans, setSpans] = useState<AgentSpan[]>([])
  const [evaluations, setEvaluations] = useState<AgentEvaluation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedSpans, setExpandedSpans] = useState<Set<number>>(new Set())

  useEffect(() => {
    if (!traceId) return

    async function fetchData() {
      setLoading(true)
      try {
        const [traceRes, spansRes, evalRes] = await Promise.all([
          getAgentTrace(traceId!),
          getAgentTraceSpans(traceId!),
          getTraceEvaluations(traceId!),
        ])
        setTrace(traceRes.data)
        setSpans(spansRes.data.items || [])
        setEvaluations(evalRes.data.items || [])
      } catch {
        setError('加载详情失败')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [traceId])

  const toggleSpan = (id: number) => {
    setExpandedSpans((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const spanTree = useMemo(() => buildSpanTree(spans), [spans])

  if (loading) {
    return (
      <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--color-muted)' }}>
        加载中...
      </div>
    )
  }

  if (error || !trace) {
    return (
      <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--color-error)' }}>
        {error || 'Trace 不存在'}
      </div>
    )
  }

  const isFailed = trace.status === 'failed'

  return (
    <div style={{ padding: 'var(--spacing-xl)', width: '100%', maxWidth: 960 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-xl)' }}>
        <button
          onClick={() => navigate('/admin/agent-monitoring')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '6px 12px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            cursor: 'pointer',
            fontSize: 13,
            color: 'var(--color-ink)',
          }}
        >
          <ArrowLeft size={14} />
          返回列表
        </button>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 24,
            fontWeight: 400,
            margin: 0,
            color: 'var(--color-ink)',
            letterSpacing: '-0.3px',
          }}
        >
          Trace 详情
        </h1>
      </div>

      {/* Trace Info Card */}
      <div
        style={{
          backgroundColor: 'var(--color-surface-card)',
          borderRadius: 'var(--rounded-lg)',
          padding: 'var(--spacing-xl)',
          marginBottom: 'var(--spacing-xl)',
          border: isFailed ? '1px solid var(--color-error)' : '1px solid var(--color-hairline)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--spacing-md)' }}>
          <code style={{ fontSize: 14, color: 'var(--color-muted)', fontFamily: 'var(--font-mono)' }}>
            {trace.trace_id}
          </code>
          <StatusBadge status={trace.status} />
          {trace.is_flagged && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 12,
                fontWeight: 500,
                color: 'var(--color-error)',
                backgroundColor: 'rgba(198, 69, 69, 0.12)',
                padding: '2px 8px',
                borderRadius: 'var(--rounded-pill)',
              }}
            >
              <AlertTriangle size={12} />
              异常标记
            </span>
          )}
          {isFailed && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--color-error)' }}>
              <AlertTriangle size={14} />
              {trace.error_type}
            </span>
          )}
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: 'var(--spacing-lg)',
          }}
        >
          <InfoItem label="用户 ID" value={trace.user_id ?? '-'} />
          <InfoItem label="对话 ID" value={trace.conversation_id ?? '-'} />
          <InfoItem label="耗时" value={formatDuration(trace.latency_ms)} />
          <InfoItem label="Token" value={`${trace.total_tokens ?? 0} (${trace.prompt_tokens ?? 0} / ${trace.completion_tokens ?? 0})`} />
          <InfoItem label="节点步数" value={trace.node_steps} />
          <InfoItem label="工具调用" value={trace.tool_calls_count} />
        </div>

        {trace.error_message && (
          <div
            style={{
              marginTop: 'var(--spacing-md)',
              padding: 'var(--spacing-md)',
              backgroundColor: 'rgba(198, 69, 69, 0.08)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 13,
              color: 'var(--color-error)',
              fontFamily: 'var(--font-mono)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {trace.error_message}
          </div>
        )}

        {/* Evaluations */}
        {evaluations.length > 0 && (
          <div
            style={{
              marginTop: 'var(--spacing-md)',
              padding: 'var(--spacing-md)',
              backgroundColor: 'var(--color-surface-soft)',
              borderRadius: 'var(--rounded-md)',
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--spacing-md)',
            }}
          >
            {evaluations.map((ev) => {
              const pct = Math.round(ev.score * 100)
              const color =
                pct >= 70
                  ? 'var(--color-success)'
                  : pct >= 40
                    ? 'var(--color-accent-amber)'
                    : 'var(--color-error)'
              const dimLabel =
                {
                  relevance: '相关性',
                  helpfulness: '有用性',
                  coherence: '连贯性',
                  tool_accuracy: '工具成功率',
                }[ev.dimension] || ev.dimension
              return (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>{dimLabel}</span>
                  <span style={{ fontSize: 14, fontWeight: 600, color }}>{pct}%</span>
                  {ev.reason && (
                    <span
                      style={{ fontSize: 11, color: 'var(--color-muted-soft)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                      title={ev.reason}
                    >
                      {ev.reason}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* User Input */}
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: 'var(--rounded-lg)',
          padding: 'var(--spacing-lg)',
          marginBottom: 'var(--spacing-xl)',
          border: '1px solid var(--color-hairline)',
        }}
      >
        <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-muted)', marginBottom: 'var(--spacing-sm)' }}>
          用户输入
        </div>
        <div style={{ fontSize: 14, color: 'var(--color-body)', lineHeight: 1.6 }}>
          {trace.input_message || '-'}
        </div>
      </div>

      {/* ReAct Flow Timeline */}
      <div style={{ marginBottom: 'var(--spacing-xl)' }}>
        <h2
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 20,
            fontWeight: 400,
            margin: '0 0 var(--spacing-lg) 0',
            color: 'var(--color-ink)',
            letterSpacing: '-0.2px',
          }}
        >
          ReAct 执行流程
        </h2>

        {spans.length === 0 ? (
          <div
            style={{
              padding: 'var(--spacing-xl)',
              textAlign: 'center',
              color: 'var(--color-muted)',
              fontSize: 14,
              backgroundColor: 'var(--color-surface-soft)',
              borderRadius: 'var(--rounded-lg)',
            }}
          >
            暂无 Span 数据
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {spanTree.roots.map((span, index) => (
              <SpanTimelineItem
                key={span.id}
                span={span}
                depth={0}
                isLast={index === spanTree.roots.length - 1}
                expandedSpans={expandedSpans}
                onToggle={toggleSpan}
                treeMode={spanTree.hasHierarchy}
              />
            ))}
          </div>
        )}
      </div>

      {/* AI Output */}
      <div
        style={{
          backgroundColor: 'var(--color-surface-card)',
          borderRadius: 'var(--rounded-lg)',
          padding: 'var(--spacing-lg)',
          border: '1px solid var(--color-hairline)',
        }}
      >
        <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-muted)', marginBottom: 'var(--spacing-sm)' }}>
          AI 最终回复
        </div>
        <div style={{ fontSize: 14, color: 'var(--color-body)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
          {trace.output_message || '-'}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    completed: 'var(--color-success)',
    failed: 'var(--color-error)',
    started: 'var(--color-accent-amber)',
  }
  const bgMap: Record<string, string> = {
    completed: 'rgba(93, 184, 114, 0.12)',
    failed: 'rgba(198, 69, 69, 0.12)',
    started: 'rgba(232, 165, 90, 0.12)',
  }
  const labelMap: Record<string, string> = {
    completed: '成功',
    failed: '失败',
    started: '进行中',
  }
  const color = colorMap[status] || 'var(--color-muted)'
  const bg = bgMap[status] || 'var(--color-surface-soft)'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 'var(--rounded-pill)',
        fontSize: 12,
        fontWeight: 500,
        color,
        backgroundColor: bg,
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: color }} />
      {labelMap[status] || status}
    </span>
  )
}

function InfoItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: 'var(--color-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>{value}</div>
    </div>
  )
}

function SpanTimelineItem({
  span,
  depth,
  isLast,
  expandedSpans,
  onToggle,
  treeMode,
}: {
  span: SpanTreeNode
  depth: number
  isLast: boolean
  expandedSpans: Set<number>
  onToggle: (id: number) => void
  treeMode: boolean
}) {
  const isExpanded = expandedSpans.has(span.id)
  const color = SPAN_TYPE_COLORS[span.span_type] || 'var(--color-muted)'
  const icon = SPAN_TYPE_ICONS[span.span_type] || <Bot size={16} />
  const label = SPAN_TYPE_LABELS[span.span_type] || span.span_type
  const webSummary = formatWebSearchSummary(span)

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, marginLeft: treeMode ? depth * 28 : 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              backgroundColor: color,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
          {!isLast && (
            <div
              style={{
                width: 2,
                flex: 1,
                backgroundColor: 'var(--color-hairline)',
                marginTop: 4,
              }}
            />
          )}
        </div>

        <div style={{ flex: 1, paddingBottom: 'var(--spacing-lg)' }}>
          <div
            onClick={() => onToggle(span.id)}
            style={{
              cursor: 'pointer',
              backgroundColor: 'var(--color-canvas)',
              borderRadius: 'var(--rounded-lg)',
              border: '1px solid var(--color-hairline)',
              padding: 'var(--spacing-md) var(--spacing-lg)',
              transition: 'background-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-ink)' }}>
                  {label}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    color: 'var(--color-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {span.span_name}
                </span>
                {webSummary && (
                  <span
                    style={{
                      fontSize: 11,
                      color: 'var(--color-accent-teal)',
                      backgroundColor: 'rgba(55, 159, 148, 0.1)',
                      padding: '2px 6px',
                      borderRadius: 'var(--rounded-pill)',
                    }}
                  >
                    {webSummary}
                  </span>
                )}
                {span.status === 'failed' && (
                  <span
                    style={{
                      fontSize: 11,
                      color: 'var(--color-error)',
                      backgroundColor: 'rgba(198, 69, 69, 0.08)',
                      padding: '2px 6px',
                      borderRadius: 'var(--rounded-pill)',
                    }}
                  >
                    失败
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>
                  {formatDuration(span.latency_ms)}
                </span>
                {isExpanded ? (
                  <ChevronDown size={16} color="var(--color-muted)" />
                ) : (
                  <ChevronRight size={16} color="var(--color-muted)" />
                )}
              </div>
            </div>

            {span.span_type === 'llm' && span.token_usage && (
              <div style={{ marginTop: 8, fontSize: 12, color: 'var(--color-muted)' }}>
                {`Tokens: ${span.token_usage.total_tokens || 0} | prompt ${span.token_usage.prompt_tokens || 0} | completion ${span.token_usage.completion_tokens || 0}`}
              </div>
            )}

            {isExpanded && (
              <div
                style={{
                  marginTop: 'var(--spacing-md)',
                  paddingTop: 'var(--spacing-md)',
                  borderTop: '1px solid var(--color-hairline-soft)',
                }}
              >
                {span.input_data && (
                  <DetailBlock label="输入" data={span.input_data} />
                )}
                {span.output_data && (
                  <DetailBlock label="输出" data={span.output_data} />
                )}
                {span.error_info && (
                  <DetailBlock label="错误" data={span.error_info} isError />
                )}
                {span.meta && (
                  <DetailBlock label="Metadata" data={span.meta} />
                )}
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--color-muted-soft)' }}>
                  开始: {formatTime(span.started_at)} {' '}
                  {span.ended_at && `· 结束: ${formatTime(span.ended_at)}`}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {span.children.map((child, index) => (
        <SpanTimelineItem
          key={child.id}
          span={child}
          depth={depth + 1}
          isLast={index === span.children.length - 1}
          expandedSpans={expandedSpans}
          onToggle={onToggle}
          treeMode={treeMode}
        />
      ))}
    </div>
  )
}

function DetailBlock({
  label,
  data,
  isError,
}: {
  label: string
  data: Record<string, unknown>
  isError?: boolean
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          fontSize: 11,
          fontWeight: 500,
          color: isError ? 'var(--color-error)' : 'var(--color-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <pre
        style={{
          margin: 0,
          padding: 'var(--spacing-sm) var(--spacing-md)',
          backgroundColor: 'var(--color-surface-dark)',
          color: 'var(--color-on-dark)',
          borderRadius: 'var(--rounded-md)',
          fontSize: 12,
          fontFamily: 'var(--font-mono)',
          lineHeight: 1.5,
          overflow: 'auto',
          maxHeight: 200,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}
