import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Shield, RefreshCw, Activity } from 'lucide-react'
import type { ContentModerationRecord } from '../../types/contentModeration'
import { getModerationRecord, retryModerationRecord } from '../../api/contentModeration'

const statusLabels: Record<string, string> = {
  pending: '待审核',
  running: '审核中',
  passed: '已通过',
  blocked: '已拦截',
  action_failed: '处置失败',
  review_failed: '审核失败',
  stale: '已过期',
}

const statusColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: 'rgba(140, 140, 140, 0.12)', text: '#888' },
  running: { bg: 'rgba(99, 149, 214, 0.15)', text: '#4a7bb7' },
  passed: { bg: 'rgba(90, 170, 120, 0.12)', text: '#3d9e5f' },
  blocked: { bg: 'rgba(198, 69, 69, 0.12)', text: '#c64545' },
  action_failed: { bg: 'rgba(198, 69, 69, 0.18)', text: '#a83232' },
  review_failed: { bg: 'rgba(232, 165, 90, 0.15)', text: '#c4842a' },
  stale: { bg: 'rgba(140, 140, 140, 0.18)', text: '#666' },
}

const targetTypeLabels: Record<string, string> = {
  user: '用户',
  blog_post: '博客',
  forum_zone: '论坛分区',
  forum_post: '论坛帖子',
  forum_reply: '论坛回复',
  comment: '评论',
}

const riskLevelLabels: Record<string, string> = {
  none: '无',
  low: '低',
  medium: '中',
  high: '高',
}

const riskLevelColors: Record<string, string> = {
  none: '#888',
  low: '#4a7bb7',
  medium: '#c4842a',
  high: '#c64545',
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        padding: 'var(--spacing-xl)',
        marginBottom: 'var(--spacing-lg)',
      }}
    >
      <h3
        style={{
          fontSize: 15,
          fontWeight: 600,
          color: 'var(--color-ink)',
          margin: '0 0 var(--spacing-md)',
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  )
}

function KeyValue({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', gap: 'var(--spacing-sm)', marginBottom: 8 }}>
      <span style={{ color: 'var(--color-muted)', fontSize: 13, minWidth: 80 }}>{label}</span>
      <span style={{ color: 'var(--color-body)', fontSize: 13, fontWeight: 500 }}>{value}</span>
    </div>
  )
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre
      style={{
        backgroundColor: 'var(--color-canvas)',
        borderRadius: 'var(--rounded-md)',
        padding: 'var(--spacing-md)',
        fontSize: 12,
        lineHeight: 1.6,
        color: 'var(--color-ink)',
        overflow: 'auto',
        maxHeight: 400,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

export default function ContentModerationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [record, setRecord] = useState<ContentModerationRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [retrying, setRetrying] = useState(false)

  const fetchRecord = async () => {
    if (!id) return
    setLoading(true)
    try {
      const res = await getModerationRecord(Number(id))
      setRecord(res.data)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRecord()
  }, [id])

  const handleRetry = async () => {
    if (!record) return
    setRetrying(true)
    try {
      await retryModerationRecord(record.id)
      fetchRecord()
    } catch {
      // handled by interceptor
    } finally {
      setRetrying(false)
    }
  }

  const formatTime = (iso: string | null) => {
    if (!iso) return '-'
    return new Date(iso).toLocaleString('zh-CN')
  }

  if (loading) {
    return (
      <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--color-muted)' }}>
        加载中…
      </div>
    )
  }

  if (!record) {
    return (
      <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--color-muted)' }}>
        记录不存在或已被删除
      </div>
    )
  }

  const sColor = statusColors[record.status] || statusColors.pending
  const canRetry = ['review_failed', 'action_failed', 'stale'].includes(record.status)

  return (
    <div style={{ padding: 'var(--spacing-xl)', width: '100%' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--spacing-xl)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <button
            onClick={() => navigate('/admin/content-moderation')}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-sm)',
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-muted)',
              cursor: 'pointer',
            }}
          >
            <ArrowLeft size={16} />
          </button>
          <Shield size={24} color="var(--color-primary)" />
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 24,
              fontWeight: 400,
              margin: 0,
              color: 'var(--color-ink)',
            }}
          >
            审核详情 #{record.id}
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          {record.trace_id && (
            <button
              onClick={() => navigate(`/admin/agent-monitoring/${record.trace_id}`)}
              style={{
                height: 36,
                padding: '0 16px',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: 'var(--color-canvas)',
                border: '1px solid var(--color-hairline)',
                color: 'var(--color-ink)',
                fontSize: 13,
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                cursor: 'pointer',
              }}
            >
              <Activity size={14} />
              查看 Trace
            </button>
          )}
          {canRetry && (
            <button
              onClick={handleRetry}
              disabled={retrying}
              style={{
                height: 36,
                padding: '0 16px',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: 'var(--color-primary)',
                border: 'none',
                color: '#fff',
                fontSize: 13,
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                cursor: retrying ? 'not-allowed' : 'pointer',
                opacity: retrying ? 0.7 : 1,
              }}
            >
              <RefreshCw size={14} />
              {retrying ? '重试中…' : '重新审核'}
            </button>
          )}
        </div>
      </div>

      {/* Basic Info */}
      <Section title="基本信息">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--spacing-md)' }}>
          <KeyValue label="任务ID" value={record.task_id} />
          <KeyValue label="对象类型" value={`${targetTypeLabels[record.target_type] || record.target_type} (#${record.target_id})`} />
          <KeyValue label="触发动作" value={record.trigger_action} />
          <KeyValue
            label="状态"
            value={
              <span
                style={{
                  display: 'inline-block',
                  padding: '3px 10px',
                  borderRadius: 'var(--rounded-pill)',
                  fontSize: 12,
                  fontWeight: 600,
                  backgroundColor: sColor.bg,
                  color: sColor.text,
                }}
              >
                {statusLabels[record.status] || record.status}
              </span>
            }
          />
          <KeyValue
            label="风险等级"
            value={
              <span style={{ color: riskLevelColors[record.risk_level], fontWeight: 600 }}>
                {riskLevelLabels[record.risk_level] || record.risk_level}
              </span>
            }
          />
          <KeyValue label="分类" value={record.categories?.join(', ') || '-'} />
          <KeyValue label="模型" value={record.model_name || '-'} />
          <KeyValue label="创建时间" value={formatTime(record.created_at)} />
          <KeyValue label="开始时间" value={formatTime(record.started_at)} />
          <KeyValue label="结束时间" value={formatTime(record.finished_at)} />
          {record.error_type && (
            <KeyValue label="错误类型" value={record.error_type} />
          )}
        </div>
        {record.error_message && (
          <div
            style={{
              marginTop: 'var(--spacing-md)',
              padding: 'var(--spacing-md)',
              backgroundColor: 'rgba(198, 69, 69, 0.08)',
              borderRadius: 'var(--rounded-md)',
              color: 'var(--color-error)',
              fontSize: 13,
            }}
          >
            {record.error_message}
          </div>
        )}
      </Section>

      {/* Original Snapshot */}
      <Section title="审核输入快照">
        <JsonBlock data={record.original_snapshot} />
      </Section>

      {/* Moderation Result */}
      {record.moderation_result && (
        <Section title="模型审核结果">
          <JsonBlock data={record.moderation_result} />
        </Section>
      )}

      {/* Action Plan */}
      {record.action_plan && (
        <Section title="处置计划">
          <JsonBlock data={record.action_plan} />
        </Section>
      )}

      {/* Action Result */}
      {record.action_result && (
        <Section title="处置执行结果">
          <JsonBlock data={record.action_result} />
        </Section>
      )}
    </div>
  )
}
