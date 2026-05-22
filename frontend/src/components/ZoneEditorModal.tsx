import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import type { ForumZone } from '../types/forum'
import type { User } from '../types/user'

interface ZoneEditorModalProps {
  zone: ForumZone | null
  users: User[]
  onClose: () => void
  onSubmit: (data: {
    zone_name: string
    slug: string
    description: string
    manager_id?: number
  }) => void
  submitting?: boolean
}

export default function ZoneEditorModal({ zone, users, onClose, onSubmit, submitting = false }: ZoneEditorModalProps) {
  const isEdit = !!zone
  const [zoneName, setZoneName] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')
  const [managerId, setManagerId] = useState<number | undefined>(undefined)

  useEffect(() => {
    if (zone) {
      setZoneName(zone.zone_name)
      setSlug(zone.slug)
      setDescription(zone.description || '')
      setManagerId(zone.manager_id)
    } else {
      setZoneName('')
      setSlug('')
      setDescription('')
      setManagerId(undefined)
    }
  }, [zone])

  const handleSubmit = () => {
    if (!zoneName.trim()) return
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
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        backgroundColor: 'rgba(20,20,19,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-xl)',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: 'var(--rounded-lg)',
          width: '100%',
          maxWidth: 520,
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(20,20,19,0.15)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: 'var(--spacing-lg) var(--spacing-xl)',
            borderBottom: '1px solid var(--color-hairline)',
          }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 500, margin: 0, color: 'var(--color-ink)' }}>
            {isEdit ? '编辑分区' : '新建分区'}
          </h2>
          <button
            onClick={onClose}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-full)',
              backgroundColor: 'var(--color-surface-card)',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-muted)',
              cursor: 'pointer',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
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
            <select
              style={inputStyle}
              value={managerId ?? ''}
              onChange={(e) => setManagerId(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">默认（当前用户）</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.username}（ID: {u.id}）
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 'var(--spacing-sm)',
            padding: 'var(--spacing-md) var(--spacing-xl)',
            borderTop: '1px solid var(--color-hairline)',
          }}
        >
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
        </div>
      </div>
    </div>
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
