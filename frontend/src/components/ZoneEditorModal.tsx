import { useState, useEffect } from 'react'
import { getUserList } from '../api/users'
import BaseModal from './BaseModal'
import type { ForumZone } from '../types/forum'
import type { User } from '../types/user'

interface ZoneEditorModalProps {
  zone: ForumZone | null
  onClose: () => void
  onSubmit: (data: {
    zone_name: string
    slug: string
    description: string
    manager_id?: number
  }) => void
  submitting?: boolean
}

export default function ZoneEditorModal({ zone, onClose, onSubmit, submitting = false }: ZoneEditorModalProps) {
  const isEdit = !!zone
  const [zoneName, setZoneName] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')
  const [managerId, setManagerId] = useState<number | undefined>(undefined)
  const [managerQuery, setManagerQuery] = useState('')
  const [managerOptions, setManagerOptions] = useState<User[]>([])
  const [managerLoading, setManagerLoading] = useState(false)
  const [managerError, setManagerError] = useState('')

  useEffect(() => {
    if (zone) {
      setZoneName(zone.zone_name)
      setSlug(zone.slug)
      setDescription(zone.description || '')
      setManagerId(zone.manager_id)
      setManagerQuery(zone.manager.username)
      setManagerOptions([])
      setManagerError('')
    } else {
      setZoneName('')
      setSlug('')
      setDescription('')
      setManagerId(undefined)
      setManagerQuery('')
      setManagerOptions([])
      setManagerError('')
    }
  }, [zone])

  useEffect(() => {
    const query = managerQuery.trim()
    if (!query) {
      setManagerOptions([])
      setManagerError('')
      return
    }

    let ignore = false
    const timer = window.setTimeout(() => {
      setManagerLoading(true)
      getUserList({ username: query, limit: 8 })
        .then((res) => {
          if (ignore) return
          setManagerOptions(res.data.items)
          setManagerError('')
        })
        .catch(() => {
          if (ignore) return
          setManagerOptions([])
          setManagerError('用户搜索失败')
        })
        .finally(() => {
          if (!ignore) setManagerLoading(false)
        })
    }, 300)

    return () => {
      ignore = true
      window.clearTimeout(timer)
    }
  }, [managerQuery])

  const handleSubmit = () => {
    if (!zoneName.trim()) return
    if (managerQuery.trim() && managerId === undefined) {
      setManagerError('请从搜索结果中选择区主，或清空输入使用默认区主')
      return
    }
    onSubmit({
      zone_name: zoneName.trim(),
      slug: slug.trim(),
      description: description.trim(),
      manager_id: managerId,
    })
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    height: 40,
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
    lineHeight: 1.4,
  }

  return (
    <BaseModal
      title={<h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 500, margin: 0 }}>{isEdit ? '编辑分区' : '新建分区'}</h2>}
      onClose={onClose}
      maxWidth={520}
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
              cursor: 'pointer',
            }}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !zoneName.trim()}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: submitting ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: submitting || !zoneName.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? '保存中…' : '保存'}
          </button>
        </>
      }
    >
      <div
        style={{
          padding: 'var(--spacing-xl)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-md)',
        }}
      >
          <div>
            <label style={labelStyle}>分区名称 *</label>
            <input type="text" placeholder="分区名称" style={inputStyle} value={zoneName} onChange={(e) => setZoneName(e.target.value)} />
          </div>
          <div>
            <label style={labelStyle}>Slug</label>
            <input type="text" placeholder="URL 标识（留空自动生成）" style={inputStyle} value={slug} onChange={(e) => setSlug(e.target.value)} />
          </div>
          <div>
            <label style={labelStyle}>描述</label>
            <textarea
              placeholder="分区描述"
              style={{
                ...inputStyle,
                height: 100,
                resize: 'vertical',
                fontFamily: 'var(--font-body)',
              }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <label style={labelStyle}>区主</label>
            <input
              type="text"
              placeholder="输入用户名搜索；留空默认当前用户"
              style={inputStyle}
              value={managerQuery}
              onChange={(e) => {
                setManagerQuery(e.target.value)
                setManagerId(undefined)
                setManagerError('')
              }}
            />
            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {managerLoading && (
                <span style={{ fontSize: 12, color: 'var(--color-muted-soft)' }}>搜索中...</span>
              )}
              {!managerLoading && managerOptions.map((u) => (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => {
                    setManagerId(u.id)
                    setManagerQuery(u.username)
                    setManagerOptions([])
                    setManagerError('')
                  }}
                  style={{
                    minHeight: 36,
                    padding: '8px 12px',
                    borderRadius: 'var(--rounded-md)',
                    border: managerId === u.id ? '1px solid var(--color-primary)' : '1px solid var(--color-hairline)',
                    backgroundColor: managerId === u.id ? 'var(--color-surface-cream-strong)' : 'var(--color-surface-card)',
                    color: 'var(--color-ink)',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: 13,
                  }}
                >
                  {u.username}（ID: {u.id}）
                </button>
              ))}
              {managerError && (
                <span style={{ fontSize: 12, color: 'var(--color-error)' }}>{managerError}</span>
              )}
            </div>
          </div>
        </div>

    </BaseModal>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  fontWeight: 500,
  color: 'var(--color-muted)',
  marginBottom: 'var(--spacing-xs)',
  textTransform: 'uppercase',
  letterSpacing: '1px',
}
