import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { UserPlus } from 'lucide-react'
import { register } from '../api/users'
import AuthBrandPanel from '../components/AuthBrandPanel'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !email.trim() || !password.trim()) {
      toast.error('请填写所有必填项')
      return
    }
    if (password !== confirmPassword) {
      toast.error('两次输入的密码不一致')
      return
    }
    if (password.length < 6) {
      toast.error('密码长度至少为 6 位')
      return
    }
    setLoading(true)
    try {
      await register({ username, email, password })
      toast.success('注册成功，请登录')
      navigate('/login', { replace: true })
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    height: 44,
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
    lineHeight: 1.4,
    outline: 'none',
    transition: 'border-color 150ms ease, box-shadow 150ms ease',
  }

  return (
    <div
      className="auth-page"
      style={{
      }}
    >
      <AuthBrandPanel slogan="加入社区，与更多开发者交流" />

      {/* Right: Form panel */}
      <div
        className="auth-form-panel"
        style={{
          backgroundColor: '#faf9f5',
          padding: 'var(--spacing-xl)',
        }}
      >
        <div style={{ width: '100%', maxWidth: 400 }}>
          {/* Header */}
          <div style={{ marginBottom: 'var(--spacing-xl)' }}>
            <UserPlus size={40} color="var(--color-primary)" style={{ marginBottom: 'var(--spacing-md)' }} />
            <h1
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 32,
                fontWeight: 400,
                color: 'var(--color-ink)',
                margin: '0 0 var(--spacing-xs)',
                letterSpacing: '-0.5px',
              }}
            >
              创建账号
            </h1>
            <p style={{ fontSize: 14, color: 'var(--color-muted)', margin: 0 }}>
              注册 DE hub 账号，开启探索之旅
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-muted)',
                  marginBottom: 'var(--spacing-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                用户名
              </label>
              <input
                type="text"
                placeholder="3~64 个字符"
                style={inputStyle}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                minLength={3}
                maxLength={64}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-primary)'
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(204, 120, 92, 0.15)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-hairline)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-muted)',
                  marginBottom: 'var(--spacing-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                邮箱
              </label>
              <input
                type="email"
                placeholder="your@email.com"
                style={inputStyle}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-primary)'
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(204, 120, 92, 0.15)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-hairline)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-muted)',
                  marginBottom: 'var(--spacing-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                密码
              </label>
              <input
                type="password"
                placeholder="至少 6 位字符"
                style={inputStyle}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                maxLength={128}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-primary)'
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(204, 120, 92, 0.15)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-hairline)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-muted)',
                  marginBottom: 'var(--spacing-xs)',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                }}
              >
                确认密码
              </label>
              <input
                type="password"
                placeholder="再次输入密码"
                style={inputStyle}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-primary)'
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(204, 120, 92, 0.15)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-hairline)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                height: 44,
                marginTop: 'var(--spacing-sm)',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: loading ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
                color: 'var(--color-on-primary)',
                fontSize: 14,
                fontWeight: 500,
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background-color 150ms ease',
              }}
            >
              {loading ? '注册中…' : '注册'}
            </button>
          </form>

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 'var(--spacing-lg)' }}>
            <span style={{ fontSize: 13, color: 'var(--color-muted)' }}>
              已有账号？{' '}
            </span>
            <Link
              to="/login"
              style={{
                fontSize: 13,
                color: 'var(--color-primary)',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              去登录
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
