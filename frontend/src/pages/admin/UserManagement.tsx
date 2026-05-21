import { useCallback, useEffect, useState } from 'react'
import { Users, Plus, Pencil, Trash2, Skull, Ban } from 'lucide-react'
import StatCard from '../../components/StatCard'
import UserFormModal from '../../components/UserFormModal'
import {
  getUserList,
  createUser,
  updateUser,
  deleteUser,
  hardDeleteUser,
} from '../../api/users'
import type { User, UserPermission, CreateUserData, UpdateUserData } from '../../types/user'

interface FilterState {
  username: string
  email: string
  permission: '' | UserPermission
  include_deleted: boolean
}

const emptyFilters: FilterState = {
  username: '',
  email: '',
  permission: '',
  include_deleted: false,
}

const permissionLabels: Record<UserPermission, { label: string; color: string; bg: string }> = {
  0: { label: '普通用户', color: 'var(--color-muted)', bg: 'var(--color-surface-soft)' },
  1: { label: '管理员', color: 'var(--color-primary)', bg: 'rgba(204, 120, 92, 0.12)' },
  2: { label: '超级管理员', color: '#a82828', bg: 'rgba(168, 40, 40, 0.1)' },
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState<FilterState>(emptyFilters)
  const [loading, setLoading] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...(filters.username && { username: filters.username }),
        ...(filters.email && { email: filters.email }),
        ...(filters.permission !== '' && { permission: filters.permission }),
        include_deleted: filters.include_deleted,
      }
      const res = await getUserList(params)
      setUsers(res.data.items)
      setTotal(res.data.total)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, filters])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleCreate = async (data: CreateUserData | UpdateUserData) => {
    try {
      await createUser(data as CreateUserData)
      setShowCreate(false)
      fetchUsers()
    } catch {
      // handled by interceptor
    }
  }

  const handleUpdate = async (data: CreateUserData | UpdateUserData) => {
    if (!editingUser) return
    try {
      await updateUser(editingUser.id, data as UpdateUserData)
      setEditingUser(null)
      fetchUsers()
    } catch {
      // handled by interceptor
    }
  }

  const handleDelete = async (user: User) => {
    if (!confirm(`确定要彻底删除用户 "${user.username}" 吗？此操作不可恢复。`)) return
    try {
      await hardDeleteUser(user.id)
      fetchUsers()
    } catch {
      // handled by interceptor
    }
  }

  const handleDeactivate = async (user: User) => {
    if (!confirm(`确定要注销用户 "${user.username}" 吗？`)) return
    try {
      await deleteUser(user.id)
      fetchUsers()
    } catch {
      // handled by interceptor
    }
  }

  const formatTime = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const totalPages = Math.ceil(total / pageSize) || 1

  const inputStyle: React.CSSProperties = {
    height: 40,
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
    lineHeight: 1.4,
    minWidth: 140,
  }

  return (
    <div style={{ padding: 'var(--spacing-xl)', width: '100%' }}>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--spacing-xl)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <Users size={24} color="var(--color-primary)" />
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 28,
              fontWeight: 400,
              margin: 0,
              color: 'var(--color-ink)',
              letterSpacing: '-0.3px',
            }}
          >
            用户管理
          </h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          style={{
            height: 40,
            padding: '0 20px',
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            fontSize: 14,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            border: 'none',
          }}
        >
          <Plus size={16} />
          创建用户
        </button>
      </div>

      {/* Stats */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--spacing-lg)',
          marginBottom: 'var(--spacing-xl)',
          flexWrap: 'wrap',
        }}
      >
        <StatCard label="用户总数" value={total} />
        <StatCard label="管理员" value={users.filter((u) => u.permission >= 1 && !u.is_deleted).length} color="var(--color-primary)" />
        <StatCard label="普通用户" value={users.filter((u) => u.permission === 0 && !u.is_deleted).length} color="var(--color-muted)" />
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 'var(--spacing-md)',
          padding: 'var(--spacing-lg)',
          backgroundColor: 'var(--color-surface-card)',
          borderRadius: 'var(--rounded-lg)',
          marginBottom: 'var(--spacing-lg)',
        }}
      >
        <input
          type="text"
          placeholder="用户名"
          style={{ ...inputStyle, minWidth: 160 }}
          value={filters.username}
          onChange={(e) => setFilters((f) => ({ ...f, username: e.target.value }))}
          onKeyDown={(e) => e.key === 'Enter' && setPage(1)}
        />
        <input
          type="text"
          placeholder="邮箱"
          style={{ ...inputStyle, minWidth: 180 }}
          value={filters.email}
          onChange={(e) => setFilters((f) => ({ ...f, email: e.target.value }))}
          onKeyDown={(e) => e.key === 'Enter' && setPage(1)}
        />
        <select
          style={inputStyle}
          value={filters.permission}
          onChange={(e) => setFilters((f) => ({ ...f, permission: e.target.value === '' ? '' : (Number(e.target.value) as UserPermission) }))}
        >
          <option value="">全部权限</option>
          <option value={0}>普通用户</option>
          <option value={1}>管理员</option>
          <option value={2}>超级管理员</option>
        </select>
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
            checked={filters.include_deleted}
            onChange={(e) => setFilters((f) => ({ ...f, include_deleted: e.target.checked }))}
            style={{ accentColor: 'var(--color-primary)' }}
          />
          包含已注销
        </label>
        <button
          onClick={() => setPage(1)}
          style={{
            height: 40,
            padding: '0 20px',
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            fontSize: 14,
            fontWeight: 500,
            border: 'none',
            marginLeft: 'auto',
          }}
        >
          查询
        </button>
      </div>

      {/* Table */}
      <div
        style={{
          backgroundColor: 'var(--color-surface-card)',
          borderRadius: 'var(--rounded-lg)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-hairline)' }}>
              <th style={{ width: 60, padding: '12px 16px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>ID</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>用户名</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>邮箱</th>
              <th style={{ width: 110, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>权限</th>
              <th style={{ width: 90, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>状态</th>
              <th style={{ width: 140, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>创建时间</th>
              <th style={{ width: 110, padding: '12px 16px', textAlign: 'right', color: 'var(--color-muted)', fontWeight: 500 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: 'var(--spacing-xxl)', textAlign: 'center', color: 'var(--color-muted)' }}>
                  加载中…
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: 'var(--spacing-xxl)', textAlign: 'center', color: 'var(--color-muted)' }}>
                  暂无数据
                </td>
              </tr>
            ) : (
              users.map((user) => {
                const perm = permissionLabels[user.permission]
                return (
                  <tr
                    key={user.id}
                    style={{
                      borderBottom: '1px solid var(--color-hairline-soft)',
                      opacity: user.is_deleted ? 0.6 : 1,
                      textDecoration: user.is_deleted ? 'line-through' : 'none',
                    }}
                  >
                    <td style={{ padding: '10px 16px', color: 'var(--color-muted)' }}>{user.id}</td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-ink)', fontWeight: 500 }}>{user.username}</td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-body)' }}>{user.email}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 10px',
                          borderRadius: 'var(--rounded-pill)',
                          fontSize: 12,
                          fontWeight: 600,
                          backgroundColor: perm.bg,
                          color: perm.color,
                        }}
                      >
                        {perm.label}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      {user.is_deleted ? (
                        <span style={{ color: 'var(--color-muted)', fontWeight: 500 }}>已注销</span>
                      ) : (
                        <span style={{ color: 'var(--color-success)', fontWeight: 500 }}>正常</span>
                      )}
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>{formatTime(user.created_at)}</td>
                    <td style={{ padding: '10px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => setEditingUser(user)}
                          title="编辑"
                          style={iconBtnStyle}
                        >
                          <Pencil size={14} />
                        </button>
                        {!user.is_deleted && (
                          <button
                            onClick={() => handleDeactivate(user)}
                            title="注销"
                            style={{
                              ...iconBtnStyle,
                              color: 'var(--color-warning)',
                            }}
                          >
                            <Ban size={14} />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(user)}
                          title={user.is_deleted ? '彻底删除' : '硬删除'}
                          style={{
                            ...iconBtnStyle,
                            color: 'var(--color-error)',
                          }}
                        >
                          {user.is_deleted ? <Skull size={14} /> : <Trash2 size={14} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: 'var(--spacing-lg)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', fontSize: 13, color: 'var(--color-muted)' }}>
          <span>每页</span>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1) }}
            style={{
              height: 32,
              padding: '0 8px',
              borderRadius: 'var(--rounded-sm)',
              border: '1px solid var(--color-hairline)',
              backgroundColor: 'var(--color-canvas)',
              color: 'var(--color-ink)',
              fontSize: 13,
            }}
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span>条</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <button
            onClick={() => setPage(page - 1)}
            disabled={page <= 1}
            style={pageBtnStyle(page <= 1)}
          >
            {'<'}
          </button>
          <span style={{ fontSize: 13, color: 'var(--color-muted)', minWidth: 80, textAlign: 'center' }}>
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages}
            style={pageBtnStyle(page >= totalPages)}
          >
            {'>'}
          </button>
        </div>
      </div>

      {/* Modals */}
      {showCreate && (
        <UserFormModal
          user={null}
          onClose={() => setShowCreate(false)}
          onSubmit={handleCreate}
        />
      )}
      {editingUser && (
        <UserFormModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSubmit={handleUpdate}
        />
      )}
    </div>
  )
}

const iconBtnStyle: React.CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: 'var(--rounded-sm)',
  backgroundColor: 'var(--color-canvas)',
  border: '1px solid var(--color-hairline)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: 'var(--color-muted)',
}

function pageBtnStyle(disabled: boolean): React.CSSProperties {
  return {
    width: 32,
    height: 32,
    borderRadius: 'var(--rounded-sm)',
    backgroundColor: 'var(--color-canvas)',
    border: '1px solid var(--color-hairline)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: disabled ? 'var(--color-muted-soft)' : 'var(--color-ink)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: 14,
    fontWeight: 500,
  }
}
