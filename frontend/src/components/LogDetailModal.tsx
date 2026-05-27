import { CheckCircle } from 'lucide-react'
import BaseModal from './BaseModal'
import type { SystemLog } from '../types/systemLog'

interface LogDetailModalProps {
  log: SystemLog | null
  onClose: () => void
  onResolve: (id: number) => void
}

export default function LogDetailModal({ log, onClose, onResolve }: LogDetailModalProps) {
  if (!log) return null

  const formatTime = (iso: string | null) => {
    if (!iso) return '-'
    const d = new Date(iso)
    return d.toLocaleString('zh-CN')
  }

  const formatJSON = (obj: Record<string, unknown> | null) => {
    if (!obj) return '-'
    return JSON.stringify(obj, null, 2)
  }

  return (
    <BaseModal
      title={
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 500, margin: 0 }}>
          日志详情 #{log.id}
        </h2>
      }
      onClose={onClose}
      maxWidth={720}
      borderRadius="xl"
      footer={
        <>
          <button
            onClick={onClose}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: 'var(--color-canvas)',
              color: 'var(--color-ink)',
              border: '1px solid var(--color-hairline)',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            关闭
          </button>
          {!log.is_resolved && (
            <button
              onClick={() => {
                onResolve(log.id)
                onClose()
              }}
              style={{
                height: 40,
                padding: '0 20px',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: 'var(--color-success)',
                color: '#fff',
                fontSize: 14,
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <CheckCircle size={16} />
              标记已处理
            </button>
          )}
        </>
      }
    >
      <div
        style={{
          padding: 'var(--spacing-xl)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-lg)',
        }}
      >
          {/* Meta grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 'var(--spacing-md)',
            }}
          >
            <MetaItem label="级别" value={log.level} />
            <MetaItem label="模块" value={log.module || '-'} />
            <MetaItem label="状态" value={log.is_resolved ? '已处理' : '未处理'} />
            <MetaItem label="用户 ID" value={log.user_id?.toString() || '-'} />
            <MetaItem label="IP" value={log.ip || '-'} />
            <MetaItem label="Trace ID" value={log.trace_id || '-'} />
          </div>

          <MetaItem label="创建时间" value={formatTime(log.created_at)} />
          {log.resolved_at && (
            <MetaItem label="处理时间" value={formatTime(log.resolved_at)} />
          )}
          {log.resolved_by && (
            <MetaItem label="处理人 ID" value={log.resolved_by.toString()} />
          )}

          {/* Message */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-muted)', marginBottom: 'var(--spacing-xs)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              消息内容
            </div>
            <div
              style={{
                padding: 'var(--spacing-md)',
                backgroundColor: 'var(--color-surface-card)',
                borderRadius: 'var(--rounded-md)',
                fontSize: 14,
                lineHeight: 1.6,
                color: 'var(--color-body)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {log.message}
            </div>
          </div>

          {/* Exception */}
          {log.exception && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-muted)', marginBottom: 'var(--spacing-xs)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                异常堆栈
              </div>
              <pre
                style={{
                  padding: 'var(--spacing-md)',
                  backgroundColor: 'var(--color-surface-dark)',
                  borderRadius: 'var(--rounded-md)',
                  fontSize: 13,
                  lineHeight: 1.6,
                  color: 'var(--color-on-dark)',
                  overflowX: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  margin: 0,
                }}
              >
                {log.exception}
              </pre>
            </div>
          )}

          {/* Extra */}
          {log.extra && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-muted)', marginBottom: 'var(--spacing-xs)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                额外上下文
              </div>
              <pre
                style={{
                  padding: 'var(--spacing-md)',
                  backgroundColor: 'var(--color-surface-dark)',
                  borderRadius: 'var(--rounded-md)',
                  fontSize: 13,
                  lineHeight: 1.6,
                  color: 'var(--color-on-dark-soft)',
                  overflowX: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  margin: 0,
                }}
              >
                {formatJSON(log.extra)}
              </pre>
            </div>
          )}
        </div>

    </BaseModal>
  )
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-muted)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '1px' }}>
        {label}
      </div>
      <div style={{ fontSize: 14, color: 'var(--color-ink)', fontWeight: 500 }}>{value}</div>
    </div>
  )
}
