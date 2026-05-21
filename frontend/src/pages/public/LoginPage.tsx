import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Terminal, Eye, EyeOff } from 'lucide-react'
import { APP_NAME } from '@/constants'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [form, setForm] = useState({ account: '', password: '', isRemember: false })

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 px-4">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Terminal className="h-5 w-5" />
          </div>
          <h1 className="text-xl font-bold">{APP_NAME}</h1>
          <p className="text-sm text-muted-foreground">登录到你的账户</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
            <div className="space-y-2">
              <label className="text-sm font-medium">账号</label>
              <Input
                placeholder="用户名或邮箱"
                value={form.account}
                onChange={(e) => setForm({ ...form, account: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">支持用户名或邮箱登录</p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">密码</label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="输入密码"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="remember"
                checked={form.isRemember}
                onChange={(e) => setForm({ ...form, isRemember: e.target.checked })}
                className="h-4 w-4 rounded border-border accent-primary"
              />
              <label htmlFor="remember" className="text-sm text-muted-foreground">记住我</label>
            </div>

            <Button type="submit" className="w-full">登录</Button>
          </form>

          <div className="mt-4 text-center text-sm">
            <span className="text-muted-foreground">还没有账户？</span>{' '}
            <Link to="/register" className="text-primary hover:underline">立即注册</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
