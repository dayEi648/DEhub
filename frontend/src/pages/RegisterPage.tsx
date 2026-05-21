import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { UserPlus } from 'lucide-react'
import { register } from '../api/users'

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
      alert('请填写所有必填项')
      return
    }
    if (password !== confirmPassword) {
      alert('两次输入的密码不一致')
      return
    }
    if (password.length < 6) {
      alert('密码长度至少为 6 位')
      return
    }
    setLoading(true)
    try {
      await register({ username, email, password })
      alert('注册成功，请登录')
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
      style={{
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
      }}
    >
      {/* Left: Brand panel */}
      <div
        style={{
          flex: 1,
          backgroundColor: 'var(--color-surface-dark)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 'var(--spacing-xxl)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Decorative shapes */}
        <div
          style={{
            position: 'absolute',
            top: '10%',
            right: '15%',
            width: 280,
            height: 280,
            borderRadius: '50%',
            backgroundColor: 'var(--color-primary)',
            opacity: 0.06,
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '20%',
            left: '10%',
            width: 160,
            height: 160,
            borderRadius: '50%',
            backgroundColor: 'var(--color-accent-teal)',
            opacity: 0.05,
          }}
        />
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 500,
            height: 500,
            borderRadius: '50%',
            border: '1px solid rgba(204, 120, 92, 0.08)',
          }}
        />

        {/* Content - centered */}
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 420 }}>
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 48,
              fontWeight: 400,
              color: 'var(--color-on-dark)',
              margin: '0 0 var(--spacing-sm)',
              letterSpacing: '-1px',
            }}
          >
            DE hub
          </h2>
          <p style={{ fontSize: 15, color: 'var(--color-on-dark-soft)', margin: '0 0 var(--spacing-xxl)', lineHeight: 1.6 }}>
            开发者的个人空间站
          </p>

          <div
            style={{
              width: 40,
              height: 3,
              backgroundColor: 'var(--color-primary)',
              borderRadius: 'var(--rounded-pill)',
              margin: '0 auto var(--spacing-xl)',
            }}
          />

          <p
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 24,
              fontWeight: 400,
              color: 'var(--color-on-dark)',
              lineHeight: 1.4,
              margin: 0,
              letterSpacing: '-0.3px',
            }}
          >
            加入社区，与更多开发者交流
          </p>
        </div>
      </div>

      {/* Right: Form panel */}
      <div
        style={{
          width: 520,
          minWidth: 520,
          backgroundColor: '#faf9f5',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
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
