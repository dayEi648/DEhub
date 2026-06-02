import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { UserCircle } from 'lucide-react'
import { login } from '../api/users'
import { setToken, setRefreshToken, setUser } from '../utils/auth'
import AuthBrandPanel from '../components/AuthBrandPanel'

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
      <AuthBrandPanel slogan="记录思考，分享技术，构建连接" />

      {/* Right: Form panel */}
      <div
        className="auth-form-panel animate-fadeInRight"
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
