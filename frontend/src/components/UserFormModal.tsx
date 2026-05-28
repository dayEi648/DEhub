import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import type { User, CreateUserData, UpdateUserData, UserPermission } from '../types/user'
import BaseModal from './BaseModal'

interface UserFormModalProps {
  user: User | null // null = create mode
  onClose: () => void
  onSubmit: (data: CreateUserData | UpdateUserData) => void
}

export default function UserFormModal({ user, onClose, onSubmit }: UserFormModalProps) {
  const isEdit = !!user
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [permission, setPermission] = useState<UserPermission>(0)
  const [personalProfile, setPersonalProfile] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      setUsername(user.username)
      setEmail(user.email)
      setPassword('')
      setPermission(user.permission)
      setPersonalProfile(user.personal_profile || '')
    } else {
      setUsername('')
      setEmail('')
      setPassword('')
      setPermission(0)
      setPersonalProfile('')
    }
  }, [user])

  const isDirty = !isEdit
    ? true
    : username.trim() !== (user?.username || '') ||
      email.trim() !== (user?.email || '') ||
      permission !== (user?.permission ?? 0) ||
      personalProfile.trim() !== (user?.personal_profile || '') ||
      password.trim().length > 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !email.trim()) {
      toast.error('请填写用户名和邮箱')
      return
    }
    if (!isEdit && !password.trim()) {
      toast.error('创建用户时必须填写密码')
      return
    }
    setLoading(true)
    try {
      if (isEdit) {
        const data: UpdateUserData = {
          username,
          email,
          permission,
          personal_profile: personalProfile || undefined,
        }
        if (password.trim()) data.password = password
        await onSubmit(data)
      } else {
        const data: CreateUserData = {
          username,
          email,
          password,
          permission,
          personal_profile: personalProfile || undefined,
        }
        await onSubmit(data)
      }
    } finally {
      setLoading(false)
    }
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
      title={
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 500, margin: 0 }}>
          {isEdit ? '编辑用户' : '创建用户'}
        </h2>
      }
      onClose={onClose}
      maxWidth={520}
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
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !isDirty}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: loading || !isDirty ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: loading || !isDirty ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '保存中…' : '保存'}
          </button>
        </>
      }
    >
      <form
        onSubmit={handleSubmit}
        style={{
          padding: 'var(--spacing-xl)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-md)',
        }}
      >
          <div>
            <label style={labelStyle}>用户名 *</label>
            <input
              type="text"
              placeholder="3~64 个字符"
              style={inputStyle}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={64}
            />
          </div>

          <div>
            <label style={labelStyle}>邮箱 *</label>
            <input
              type="email"
              placeholder="your@email.com"
              style={inputStyle}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={labelStyle}>{isEdit ? '密码（留空则不修改）' : '密码 *'}</label>
            <input
              type="password"
              placeholder={isEdit ? '留空表示不修改' : '至少 6 位字符'}
              style={inputStyle}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required={!isEdit}
              minLength={isEdit ? undefined : 6}
              maxLength={128}
            />
          </div>

          <div>
            <label style={labelStyle}>权限级别</label>
            <select
              style={inputStyle}
              value={permission}
              onChange={(e) => setPermission(Number(e.target.value) as UserPermission)}
            >
              <option value={0}>普通用户</option>
              <option value={1}>管理员</option>
              <option value={2}>超级管理员</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>个人简介</label>
            <textarea
              placeholder="选填"
              style={{
                ...inputStyle,
                height: 80,
                resize: 'vertical',
                fontFamily: 'var(--font-body)',
              }}
              value={personalProfile}
              onChange={(e) => setPersonalProfile(e.target.value)}
            />
          </div>
        </form>

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
