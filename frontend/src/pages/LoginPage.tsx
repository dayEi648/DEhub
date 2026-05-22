import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { UserCircle } from 'lucide-react'
import { login } from '../api/users'
import { setToken, setRefreshToken, setUser } from '../utils/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const [account, setAccount] = useState('')
  const [password, setPassword] = useState('')
  const [isRemember, setIsRemember] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!account.trim() || !password.trim()) {
      toast.error('请填写账号和密码')
      return
    }
    setLoading(true)
    try {
      const res = await login({ account, password, is_remember: isRemember })
      setToken(res.data.access_token)
      if (res.data.refresh_token) {
        setRefreshToken(res.data.refresh_token)
      }
      setUser(res.data.user)
      navigate('/', { replace: true })
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
      {/* Left: Brand panel */}
      <div
        className="auth-brand-panel"
        style={{
          backgroundColor: 'var(--color-surface-dark)',
          flexDirection: 'column',
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
            记录思考，分享技术，构建连接
          </p>
        </div>
      </div>

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
            <UserCircle size={40} color="var(--color-primary)" style={{ marginBottom: 'var(--spacing-md)' }} />
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
              欢迎回来
            </h1>
            <p style={{ fontSize: 14, color: 'var(--color-muted)', margin: 0 }}>
              登录到 DE hub
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
                账号
              </label>
              <input
                type="text"
                placeholder="用户名或邮箱"
                style={inputStyle}
                value={account}
                onChange={(e) => setAccount(e.target.value)}
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
                placeholder="请输入密码"
                style={inputStyle}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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

            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-xs)',
                fontSize: 13,
                color: 'var(--color-muted)',
                cursor: 'pointer',
                userSelect: 'none',
              }}
            >
              <input
                type="checkbox"
                checked={isRemember}
                onChange={(e) => setIsRemember(e.target.checked)}
                style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
              />
              记住登录
            </label>

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
              {loading ? '登录中…' : '登录'}
            </button>
          </form>

          {/* Footer */}
          <div style={{ textAlign: 'center', marginTop: 'var(--spacing-lg)' }}>
            <span style={{ fontSize: 13, color: 'var(--color-muted)' }}>
              还没有账号？{' '}
            </span>
            <Link
              to="/register"
              style={{
                fontSize: 13,
                color: 'var(--color-primary)',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              去注册
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
