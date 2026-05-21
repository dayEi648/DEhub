import { useState } from 'react'
import { Search, Filter, Trash2, UserX, Edit } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import Pagination from '@/components/ui/Pagination'
import Modal from '@/components/ui/Modal'
import { PERMISSION_LABELS } from '@/constants'
import { cn } from '@/lib/utils'
import { formatDateTime } from '@/lib/utils'

const MOCK_USERS = [
  { id: 1, username: 'admin', email: 'admin@dehub.dev', permission: 2, is_deleted: false, avatar_url: null, personal_profile: '超级管理员', created_at: '2024-01-01T00:00:00' },
  { id: 2, username: 'moderator', email: 'mod@dehub.dev', permission: 1, is_deleted: false, avatar_url: null, personal_profile: '内容管理员', created_at: '2024-01-02T00:00:00' },
  { id: 3, username: 'CodeMaster', email: 'code@example.com', permission: 0, is_deleted: false, avatar_url: null, personal_profile: '热爱编程', created_at: '2024-01-05T10:00:00' },
  { id: 4, username: 'DevNewbie', email: 'newbie@example.com', permission: 0, is_deleted: false, avatar_url: null, personal_profile: '正在学习中', created_at: '2024-01-10T08:00:00' },
  { id: 5, username: 'InactiveUser', email: 'inactive@example.com', permission: 0, is_deleted: true, avatar_url: null, personal_profile: null, created_at: '2024-01-12T00:00:00' },
]

export default function AdminUsersPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterPermission, setFilterPermission] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [editUser, setEditUser] = useState<typeof MOCK_USERS[0] | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">用户管理</h1>
        <p className="text-sm text-muted-foreground">管理系统用户账户</p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="搜索用户名或邮箱..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">权限：</span>
              <button
                onClick={() => setFilterPermission(null)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterPermission === null ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                全部
              </button>
              {[0, 1, 2].map(p => (
                <button
                  key={p}
                  onClick={() => setFilterPermission(p)}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-sm transition-colors',
                    filterPermission === p ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  )}
                >
                  {PERMISSION_LABELS[p]}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">ID</th>
                  <th className="px-4 py-3 text-left font-medium">用户名</th>
                  <th className="px-4 py-3 text-left font-medium">邮箱</th>
                  <th className="px-4 py-3 text-left font-medium">权限</th>
                  <th className="px-4 py-3 text-left font-medium">状态</th>
                  <th className="px-4 py-3 text-left font-medium">注册时间</th>
                  <th className="px-4 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_USERS.map(user => (
                  <tr key={user.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">{user.id}</td>
                    <td className="px-4 py-3 font-medium">{user.username}</td>
                    <td className="px-4 py-3 text-muted-foreground">{user.email}</td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={user.permission === 2 ? 'default' : user.permission === 1 ? 'secondary' : 'outline'}
                      >
                        {PERMISSION_LABELS[user.permission]}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      {user.is_deleted ? (
                        <Badge variant="destructive">已注销</Badge>
                      ) : (
                        <Badge variant="outline" className="text-emerald-500 border-emerald-500/20">正常</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{formatDateTime(user.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setEditUser(user)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                          <UserX className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex justify-center">
        <Pagination currentPage={currentPage} totalPages={5} onPageChange={setCurrentPage} />
      </div>

      {/* Edit Modal */}
      <Modal
        open={!!editUser}
        onClose={() => setEditUser(null)}
        title="编辑用户"
      >
        {editUser && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">用户名</label>
              <Input defaultValue={editUser.username} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">邮箱</label>
              <Input defaultValue={editUser.email} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">权限</label>
              <select className="mt-1 flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm">
                <option value={0}>普通用户</option>
                <option value={1}>管理员</option>
                <option value={2}>超级管理员</option>
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditUser(null)}>取消</Button>
              <Button>保存</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
