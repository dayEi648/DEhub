import { useState } from 'react'
import { Lock, Moon, Sun, Monitor } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  })

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-6">设置</h1>

      {/* Appearance */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>外观</CardTitle>
          <CardDescription>自定义网站的主题显示</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => setTheme('light')}
              className={cn(
                'flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors',
                theme === 'light' ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted'
              )}
            >
              <Sun className="h-6 w-6" />
              <span className="text-sm font-medium">浅色</span>
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={cn(
                'flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors',
                theme === 'dark' ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted'
              )}
            >
              <Moon className="h-6 w-6" />
              <span className="text-sm font-medium">深色</span>
            </button>
            <button
              onClick={() => setTheme('light')}
              className={cn(
                'flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors opacity-50 cursor-not-allowed',
                false ? 'border-primary bg-primary/5' : 'border-border'
              )}
              title="跟随系统（开发中）"
            >
              <Monitor className="h-6 w-6" />
              <span className="text-sm font-medium">系统</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle>修改密码</CardTitle>
          <CardDescription>修改成功后需要重新登录</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
            <div className="space-y-2">
              <label className="text-sm font-medium">当前密码</label>
              <Input
                type="password"
                placeholder="输入当前密码"
                value={passwordForm.old_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">新密码</label>
              <Input
                type="password"
                placeholder="6-128个字符"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">确认新密码</label>
              <Input
                type="password"
                placeholder="再次输入新密码"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
              />
            </div>
            <Button type="submit" className="gap-1">
              <Lock className="h-4 w-4" />
              修改密码
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
