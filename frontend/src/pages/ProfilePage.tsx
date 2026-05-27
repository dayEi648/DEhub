import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  ArrowLeft,
  User as UserIcon,
  Camera,
  Mail,
  Calendar,
  Lock,
  Eye,
  EyeOff,
  Save,
  X,
  Pencil,
  Shield,
  MessageSquare,
  LayoutGrid,
  Trash2,
  BookOpen,
} from 'lucide-react'
import { getUserDetail, updateUser, changePassword } from '../api/users'
import {
  getFavoriteBlogPosts,
  getFavoriteForumPosts,
  getFollowedZones,
  unfavoriteBlogPost,
  unfavoriteForumPost,
  unfollowZone,
} from '../api/favorites'
import { getUser as getStoredUser, setUser, clearAuth } from '../utils/auth'
import { formatDateCN } from '../utils/format'
import type { User as UserType } from '../types/user'
import type { BlogPostListItem } from '../types/blog'
import type { ForumPostListItem, ForumZone } from '../types/forum'

import { parseErrorMessage } from '../utils/error'
import { validateImageFile, createImagePreview } from '../utils/upload'
import UserAvatar from '../components/UserAvatar'

type TabKey = 'profile' | 'security' | 'favorites'
type FavSubTab = 'zones' | 'posts' | 'blogs'

/* ─── Components ─── */

function TabNav({
  active,
  onChange,
}: {
  active: TabKey
  onChange: (k: TabKey) => void
}) {
  const tabs: { key: TabKey; label: string }[] = [
    { key: 'profile', label: '个人资料' },
    { key: 'security', label: '账户安全' },
    { key: 'favorites', label: '我的收藏' },
  ]

  return (
    <div
      style={{
        display: 'flex',
        gap: 'var(--spacing-xs)',
        marginBottom: 'var(--spacing-xl)',
        borderBottom: '1px solid var(--color-hairline-soft)',
      }}
    >
      {tabs.map((t) => {
        const isActive = active === t.key
        return (
          <button
            key={t.key}
            onClick={() => onChange(t.key)}
            style={{
              padding: '10px 16px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: isActive ? 'var(--color-surface-card)' : 'transparent',
              color: isActive ? 'var(--color-ink)' : 'var(--color-muted)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              marginBottom: -1,
              borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
              transition: 'all 150ms ease',
            }}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}

function InputField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  disabled = false,
  multiline = false,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  type?: string
  placeholder?: string
  disabled?: boolean
  multiline?: boolean
}) {
  const baseStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: disabled ? 'var(--color-surface-soft)' : 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
    lineHeight: 1.4,
    outline: 'none',
    transition: 'border-color 150ms ease, box-shadow 150ms ease',
    fontFamily: 'var(--font-body)',
  }

  return (
    <div style={{ marginBottom: 'var(--spacing-md)' }}>
      <label
        style={{
          display: 'block',
          fontSize: 12,
          fontWeight: 500,
          color: 'var(--color-muted)',
          marginBottom: 'var(--spacing-xs)',
          textTransform: 'uppercase' as const,
          letterSpacing: '1px',
        }}
      >
        {label}
      </label>
      {multiline ? (
        <textarea
          style={{ ...baseStyle, minHeight: 80, resize: 'vertical' }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onFocus={(e) => {
            if (!disabled) e.currentTarget.style.borderColor = 'var(--color-primary)'
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-hairline)'
          }}
        />
      ) : (
        <input
          type={type}
          style={baseStyle}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          onFocus={(e) => {
            if (!disabled) e.currentTarget.style.borderColor = 'var(--color-primary)'
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-hairline)'
          }}
        />
      )}
    </div>
  )
}

function PasswordField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  const [show, setShow] = useState(false)

  return (
    <div style={{ marginBottom: 'var(--spacing-md)', position: 'relative' }}>
      <label
        style={{
          display: 'block',
          fontSize: 12,
          fontWeight: 500,
          color: 'var(--color-muted)',
          marginBottom: 'var(--spacing-xs)',
          textTransform: 'uppercase' as const,
          letterSpacing: '1px',
        }}
      >
        {label}
      </label>
      <div style={{ position: 'relative' }}>
        <input
          type={show ? 'text' : 'password'}
          style={{
            width: '100%',
            padding: '10px 40px 10px 14px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            color: 'var(--color-ink)',
            fontSize: 14,
            lineHeight: 1.4,
            outline: 'none',
            transition: 'border-color 150ms ease',
            fontFamily: 'var(--font-body)',
          }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-primary)'
            e.currentTarget.style.boxShadow = '0 0 0 3px rgba(204, 120, 92, 0.15)'
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-hairline)'
            e.currentTarget.style.boxShadow = 'none'
          }}
        />
        <button
          type="button"
          onClick={() => setShow(!show)}
          style={{
            position: 'absolute',
            right: 10,
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-muted)',
            display: 'flex',
            alignItems: 'center',
            padding: 4,
          }}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </div>
  )
}

/* ─── Main Page ─── */

export default function ProfilePage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const currentUser = getStoredUser()
  const userId = currentUser?.id

  const [user, setUserState] = useState<UserType | null>(currentUser)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabKey>('profile')

  // Edit profile state
  const [isEditing, setIsEditing] = useState(false)
  const [editUsername, setEditUsername] = useState('')
  const [editEmail, setEditEmail] = useState('')
  const [editProfile, setEditProfile] = useState('')
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [savingProfile, setSavingProfile] = useState(false)

  // Password state
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [savingPassword, setSavingPassword] = useState(false)

  // Favorites state
  const [favoriteBlogs, setFavoriteBlogs] = useState<BlogPostListItem[]>([])
  const [favoritePosts, setFavoritePosts] = useState<ForumPostListItem[]>([])
  const [followedZones, setFollowedZones] = useState<ForumZone[]>([])
  const [loadingFavorites, setLoadingFavorites] = useState(false)
  const [favSubTab, setFavSubTab] = useState<FavSubTab>('zones')

  const fetchUser = useCallback(async () => {
    if (!userId) return
    try {
      setLoading(true)
      const res = await getUserDetail(userId)
      setUserState(res.data)
      setUser(res.data)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    if (!userId) {
      navigate('/login', { replace: true })
      return
    }
    fetchUser()
  }, [fetchUser, navigate, userId])

  const startEdit = () => {
    if (!user) return
    setEditUsername(user.username)
    setEditEmail(user.email)
    setEditProfile(user.personal_profile || '')
    setAvatarFile(null)
    setAvatarPreview(null)
    setIsEditing(true)
  }

  const cancelEdit = () => {
    setIsEditing(false)
    setAvatarFile(null)
    setAvatarPreview(null)
  }

  const handleAvatarClick = () => {
    if (!isEditing) return
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const error = validateImageFile(file)
    if (error) {
      toast.error(error)
      return
    }

    setAvatarFile(file)
    try {
      const preview = await createImagePreview(file)
      setAvatarPreview(preview)
    } catch {
      toast.error('图片预览生成失败')
    }
  }

  const saveProfile = async () => {
    if (!userId) return
    if (!editUsername.trim()) {
      toast.error('用户名不能为空')
      return
    }
    if (!editEmail.trim()) {
      toast.error('邮箱不能为空')
      return
    }

    setSavingProfile(true)
    try {
      const userIn = {
        username: editUsername.trim(),
        email: editEmail.trim(),
        personal_profile: editProfile.trim() || undefined,
      }

      const res = await updateUser(userId, userIn, avatarFile || undefined)
      setUserState(res.data)
      setUser(res.data)
      setIsEditing(false)
      setAvatarFile(null)
      setAvatarPreview(null)
      toast.success('个人资料已更新')
    } catch (err: unknown) {
      toast.error(parseErrorMessage(err, '更新失败，请重试'))
    } finally {
      setSavingProfile(false)
    }
  }

  const savePassword = async () => {
    if (!oldPassword) {
      toast.error('请输入旧密码')
      return
    }
    if (!newPassword || newPassword.length < 6) {
      toast.error('新密码至少 6 位')
      return
    }
    if (newPassword === oldPassword) {
      toast.error('新密码不能与旧密码相同')
      return
    }
    if (newPassword !== confirmPassword) {
      toast.error('两次输入的新密码不一致')
      return
    }

    setSavingPassword(true)
    try {
      await changePassword({ old_password: oldPassword, new_password: newPassword })
      toast.success('密码已修改，请重新登录')
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => {
        clearAuth()
        navigate('/login', { replace: true })
      }, 1500)
    } catch (err: unknown) {
      toast.error(parseErrorMessage(err, '密码修改失败，请重试'))
    } finally {
      setSavingPassword(false)
    }
  }

  // Favorites
  const fetchFavorites = useCallback(async () => {
    try {
      setLoadingFavorites(true)
      const [blogRes, postRes, zoneRes] = await Promise.all([
        getFavoriteBlogPosts({ limit: 20 }),
        getFavoriteForumPosts({ limit: 20 }),
        getFollowedZones({ limit: 20 }),
      ])
      setFavoriteBlogs(blogRes.data.items || [])
      setFavoritePosts(postRes.data.items || [])
      setFollowedZones(zoneRes.data.items || [])
    } catch {
      // handled by interceptor
    } finally {
      setLoadingFavorites(false)
    }
  }, [])

  useEffect(() => {
    if (activeTab === 'favorites') {
      fetchFavorites()
    }
  }, [activeTab, fetchFavorites])

  const handleUnfavoriteBlog = async (postId: number) => {
    try {
      await unfavoriteBlogPost(postId)
      setFavoriteBlogs((prev) => prev.filter((b) => b.id !== postId))
      toast.success('已取消收藏')
    } catch (err: unknown) {
      toast.error(parseErrorMessage(err, '操作失败'))
    }
  }

  const handleUnfavoritePost = async (postId: number) => {
    try {
      await unfavoriteForumPost(postId)
      setFavoritePosts((prev) => prev.filter((p) => p.id !== postId))
      toast.success('已取消收藏')
    } catch (err: unknown) {
      toast.error(parseErrorMessage(err, '操作失败'))
    }
  }

  const handleUnfollowZone = async (zoneId: number) => {
    try {
      await unfollowZone(zoneId)
      setFollowedZones((prev) => prev.filter((z) => z.id !== zoneId))
      toast.success('已取消关注')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
      toast.error(msg || '操作失败')
    }
  }

  if (loading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-muted)',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: 40,
              height: 40,
              border: '3px solid var(--color-hairline)',
              borderTopColor: 'var(--color-primary)',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
              margin: '0 auto var(--spacing-md)',
            }}
          />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <span style={{ fontSize: 14 }}>加载中…</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div
        style={{
          minHeight: '100vh',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-error)',
        }}
      >
        无法加载用户信息
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-canvas)' }}>
      {/* Top bar */}
      <header
        style={{
          height: 64,
          backgroundColor: 'var(--color-canvas)',
          borderBottom: '1px solid var(--color-hairline-soft)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 var(--spacing-xl)',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        <button
          onClick={() => navigate('/')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--color-muted)',
            fontSize: 14,
            fontWeight: 500,
            transition: 'color 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--color-ink)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--color-muted)'
          }}
        >
          <ArrowLeft size={18} />
          返回首页
        </button>
      </header>

      {/* Content */}
      <main
        style={{
          maxWidth: 720,
          margin: '0 auto',
          padding: 'var(--spacing-xl) var(--spacing-md)',
        }}
      >
        {/* Page title */}
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(28px, 4vw, 36px)',
            fontWeight: 400,
            letterSpacing: '-0.5px',
            color: 'var(--color-ink)',
            margin: '0 0 var(--spacing-xl)',
          }}
        >
          个人空间
        </h1>

        {/* Avatar + username summary */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-md)',
            marginBottom: 'var(--spacing-xl)',
          }}
        >
          <div style={{ position: 'relative' }}>
            <UserAvatar
              url={user.avatar_url}
              name={user.username}
              size={64}
              iconSize={28}
              style={{ border: '2px solid var(--color-hairline)' }}
            />
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 500, color: 'var(--color-ink)' }}>
              {user.username}
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-muted)', marginTop: 2 }}>
              {user.email}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <TabNav active={activeTab} onChange={setActiveTab} />

        {/* Tab: Profile */}
        {activeTab === 'profile' && (
          <div
            style={{
              backgroundColor: 'var(--color-surface-card)',
              borderRadius: 'var(--rounded-lg)',
              padding: 'var(--spacing-xl)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 'var(--spacing-lg)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                <UserIcon size={18} color="var(--color-primary)" />
                <h2
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: 20,
                    fontWeight: 400,
                    letterSpacing: '-0.3px',
                    color: 'var(--color-ink)',
                    margin: 0,
                  }}
                >
                  个人资料
                </h2>
              </div>
              {!isEditing && (
                <button
                  onClick={startEdit}
                  style={{
                    height: 36,
                    padding: '0 16px',
                    borderRadius: 'var(--rounded-md)',
                    backgroundColor: 'var(--color-canvas)',
                    color: 'var(--color-ink)',
                    fontSize: 13,
                    fontWeight: 500,
                    border: '1px solid var(--color-hairline)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    transition: 'background-color 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
                  }}
                >
                  <Pencil size={14} />
                  编辑资料
                </button>
              )}
            </div>

            {/* Avatar upload (only in edit mode) */}
            {isEditing && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  marginBottom: 'var(--spacing-lg)',
                }}
              >
                <div
                  style={{
                    position: 'relative',
                    width: 96,
                    height: 96,
                    cursor: 'pointer',
                  }}
                  onClick={handleAvatarClick}
                >
                  {(avatarPreview || user.avatar_url) ? (
                    <img
                      src={avatarPreview || user.avatar_url || undefined}
                      alt="avatar"
                      style={{
                        width: 96,
                        height: 96,
                        borderRadius: '50%',
                        objectFit: 'cover',
                        border: '2px solid var(--color-hairline)',
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: 96,
                        height: 96,
                        borderRadius: '50%',
                        backgroundColor: 'var(--color-canvas)',
                        border: '2px solid var(--color-hairline)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--color-primary)',
                      }}
                    >
                      <UserIcon size={40} />
                    </div>
                  )}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      right: 0,
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      backgroundColor: 'var(--color-primary)',
                      color: '#fff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '2px solid var(--color-canvas)',
                    }}
                  >
                    <Camera size={16} />
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
              </div>
            )}

            {isEditing ? (
              <>
                <InputField
                  label="用户名"
                  value={editUsername}
                  onChange={setEditUsername}
                  placeholder="请输入用户名"
                />
                <InputField
                  label="邮箱"
                  value={editEmail}
                  onChange={setEditEmail}
                  placeholder="请输入邮箱"
                />
                <InputField
                  label="个人简介"
                  value={editProfile}
                  onChange={setEditProfile}
                  placeholder="介绍一下自己吧"
                  multiline
                />
                <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-sm)' }}>
                  <button
                    onClick={saveProfile}
                    disabled={savingProfile}
                    style={{
                      height: 40,
                      padding: '0 20px',
                      borderRadius: 'var(--rounded-md)',
                      backgroundColor: savingProfile ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
                      color: 'var(--color-on-primary)',
                      fontSize: 14,
                      fontWeight: 500,
                      border: 'none',
                      cursor: savingProfile ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      transition: 'background-color 150ms ease',
                    }}
                  >
                    <Save size={15} />
                    {savingProfile ? '保存中…' : '保存'}
                  </button>
                  <button
                    onClick={cancelEdit}
                    disabled={savingProfile}
                    style={{
                      height: 40,
                      padding: '0 20px',
                      borderRadius: 'var(--rounded-md)',
                      backgroundColor: 'var(--color-canvas)',
                      color: 'var(--color-ink)',
                      fontSize: 14,
                      fontWeight: 500,
                      border: '1px solid var(--color-hairline)',
                      cursor: savingProfile ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <X size={15} />
                    取消
                  </button>
                </div>
              </>
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 'var(--spacing-md)',
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--color-muted)',
                      marginBottom: 4,
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                    }}
                  >
                    用户名
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      color: 'var(--color-body-strong)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <UserIcon size={14} color="var(--color-primary)" />
                    {user.username}
                  </div>
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--color-muted)',
                      marginBottom: 4,
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                    }}
                  >
                    邮箱
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      color: 'var(--color-body-strong)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <Mail size={14} color="var(--color-primary)" />
                    {user.email}
                  </div>
                </div>
                <div style={{ gridColumn: '1 / -1' }}>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--color-muted)',
                      marginBottom: 4,
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                    }}
                  >
                    个人简介
                  </div>
                  <div style={{ fontSize: 15, color: 'var(--color-body)', lineHeight: 1.55 }}>
                    {user.personal_profile || (
                      <span style={{ color: 'var(--color-muted-soft)', fontStyle: 'italic' }}>
                        暂无简介
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: 'var(--color-muted)',
                      marginBottom: 4,
                      textTransform: 'uppercase',
                      letterSpacing: '1px',
                    }}
                  >
                    注册时间
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      color: 'var(--color-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <Calendar size={14} />
                    {formatDateCN(user.created_at)}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab: Security */}
        {activeTab === 'security' && (
          <div
            style={{
              backgroundColor: 'var(--color-surface-card)',
              borderRadius: 'var(--rounded-lg)',
              padding: 'var(--spacing-xl)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-sm)',
                marginBottom: 'var(--spacing-lg)',
              }}
            >
              <Shield size={18} color="var(--color-primary)" />
              <h2
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: 20,
                  fontWeight: 400,
                  letterSpacing: '-0.3px',
                  color: 'var(--color-ink)',
                  margin: 0,
                }}
              >
                账户安全
              </h2>
            </div>

            <div style={{ marginBottom: 'var(--spacing-md)' }}>
              <div
                style={{
                  fontSize: 14,
                  fontWeight: 500,
                  color: 'var(--color-body-strong)',
                  marginBottom: 'var(--spacing-xs)',
                }}
              >
                修改密码
              </div>
              <p style={{ fontSize: 13, color: 'var(--color-muted)', margin: '0 0 var(--spacing-md)' }}>
                修改成功后，所有已登录设备将被登出，需使用新密码重新登录。
              </p>
            </div>

            <PasswordField
              label="当前密码"
              value={oldPassword}
              onChange={setOldPassword}
              placeholder="请输入当前密码"
            />
            <PasswordField
              label="新密码"
              value={newPassword}
              onChange={setNewPassword}
              placeholder="至少 6 位字符"
            />
            <PasswordField
              label="确认新密码"
              value={confirmPassword}
              onChange={setConfirmPassword}
              placeholder="再次输入新密码"
            />

            <button
              onClick={savePassword}
              disabled={savingPassword}
              style={{
                height: 40,
                padding: '0 20px',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: savingPassword ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
                color: 'var(--color-on-primary)',
                fontSize: 14,
                fontWeight: 500,
                border: 'none',
                cursor: savingPassword ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                marginTop: 'var(--spacing-sm)',
                transition: 'background-color 150ms ease',
              }}
            >
              <Lock size={15} />
              {savingPassword ? '保存中…' : '修改密码'}
            </button>
          </div>
        )}

        {/* Tab: Favorites */}
        {activeTab === 'favorites' && (
          <div>
            {/* Sub tabs */}
            <div
              style={{
                display: 'flex',
                gap: 'var(--spacing-xs)',
                marginBottom: 'var(--spacing-lg)',
              }}
            >
              {([
                { key: 'zones' as FavSubTab, label: `论坛分区 (${followedZones.length})` },
                { key: 'posts' as FavSubTab, label: `论坛帖子 (${favoritePosts.length})` },
                { key: 'blogs' as FavSubTab, label: `博客文章 (${favoriteBlogs.length})` },
              ]).map((t) => {
                const isActive = favSubTab === t.key
                return (
                  <button
                    key={t.key}
                    onClick={() => setFavSubTab(t.key)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 'var(--rounded-md)',
                      backgroundColor: isActive ? 'var(--color-surface-card)' : 'transparent',
                      color: isActive ? 'var(--color-ink)' : 'var(--color-muted)',
                      fontSize: 13,
                      fontWeight: 500,
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 150ms ease',
                    }}
                  >
                    {t.label}
                  </button>
                )
              })}
            </div>

            {loadingFavorites ? (
              <div style={{ textAlign: 'center', padding: 'var(--spacing-xl)', color: 'var(--color-muted)' }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    border: '3px solid var(--color-hairline)',
                    borderTopColor: 'var(--color-primary)',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                    margin: '0 auto var(--spacing-md)',
                  }}
                />
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                <span style={{ fontSize: 14 }}>加载收藏中…</span>
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: 'var(--color-surface-card)',
                  borderRadius: 'var(--rounded-lg)',
                  padding: 'var(--spacing-xl)',
                }}
              >
                {/* SubTab: Zones */}
                {favSubTab === 'zones' && (
                  <>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-sm)',
                        marginBottom: 'var(--spacing-md)',
                      }}
                    >
                      <LayoutGrid size={18} color="var(--color-primary)" />
                      <h2
                        style={{
                          fontFamily: 'var(--font-display)',
                          fontSize: 20,
                          fontWeight: 400,
                          letterSpacing: '-0.3px',
                          color: 'var(--color-ink)',
                          margin: 0,
                        }}
                      >
                        收藏的论坛分区
                      </h2>
                    </div>
                    {followedZones.length === 0 ? (
                      <p style={{ fontSize: 14, color: 'var(--color-muted)', margin: 0, textAlign: 'center', padding: 'var(--spacing-lg)' }}>
                        暂无关注的分区
                      </p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
                        {followedZones.map((zone) => (
                          <div
                            key={zone.id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '12px 16px',
                              borderRadius: 'var(--rounded-md)',
                              backgroundColor: 'var(--color-canvas)',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                              <div
                                style={{
                                  width: 36,
                                  height: 36,
                                  borderRadius: 'var(--rounded-md)',
                                  backgroundColor: 'var(--color-surface-soft)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  color: 'var(--color-primary)',
                                }}
                              >
                                <LayoutGrid size={16} />
                              </div>
                              <div>
                                <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-body-strong)' }}>
                                  {zone.zone_name}
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--color-muted-soft)', marginTop: 2 }}>
                                  {zone.description || '暂无描述'}
                                </div>
                              </div>
                            </div>
                            <button
                              onClick={() => handleUnfollowZone(zone.id)}
                              style={{
                                width: 32,
                                height: 32,
                                borderRadius: 'var(--rounded-full)',
                                backgroundColor: 'transparent',
                                border: '1px solid var(--color-hairline)',
                                color: 'var(--color-muted)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 150ms ease',
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = 'var(--color-error)'
                                e.currentTarget.style.color = '#fff'
                                e.currentTarget.style.borderColor = 'var(--color-error)'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'transparent'
                                e.currentTarget.style.color = 'var(--color-muted)'
                                e.currentTarget.style.borderColor = 'var(--color-hairline)'
                              }}
                              title="取消关注"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {/* SubTab: Posts */}
                {favSubTab === 'posts' && (
                  <>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-sm)',
                        marginBottom: 'var(--spacing-md)',
                      }}
                    >
                      <MessageSquare size={18} color="var(--color-primary)" />
                      <h2
                        style={{
                          fontFamily: 'var(--font-display)',
                          fontSize: 20,
                          fontWeight: 400,
                          letterSpacing: '-0.3px',
                          color: 'var(--color-ink)',
                          margin: 0,
                        }}
                      >
                        收藏的论坛帖子
                      </h2>
                    </div>
                    {favoritePosts.length === 0 ? (
                      <p style={{ fontSize: 14, color: 'var(--color-muted)', margin: 0, textAlign: 'center', padding: 'var(--spacing-lg)' }}>
                        暂无收藏的帖子
                      </p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
                        {favoritePosts.map((post) => (
                          <div
                            key={post.id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '12px 16px',
                              borderRadius: 'var(--rounded-md)',
                              backgroundColor: 'var(--color-canvas)',
                            }}
                          >
                            <div style={{ minWidth: 0, flex: 1 }}>
                              <div
                                style={{
                                  fontSize: 14,
                                  fontWeight: 500,
                                  color: 'var(--color-body-strong)',
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                }}
                              >
                                {post.title}
                              </div>
                              <div style={{ fontSize: 12, color: 'var(--color-muted-soft)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span>{post.user.username}</span>
                                <span>·</span>
                                <span>{formatDateCN(post.created_at)}</span>
                              </div>
                            </div>
                            <button
                              onClick={() => handleUnfavoritePost(post.id)}
                              style={{
                                width: 32,
                                height: 32,
                                borderRadius: 'var(--rounded-full)',
                                backgroundColor: 'transparent',
                                border: '1px solid var(--color-hairline)',
                                color: 'var(--color-muted)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 150ms ease',
                                flexShrink: 0,
                                marginLeft: 'var(--spacing-sm)',
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = 'var(--color-error)'
                                e.currentTarget.style.color = '#fff'
                                e.currentTarget.style.borderColor = 'var(--color-error)'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'transparent'
                                e.currentTarget.style.color = 'var(--color-muted)'
                                e.currentTarget.style.borderColor = 'var(--color-hairline)'
                              }}
                              title="取消收藏"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {/* SubTab: Blogs */}
                {favSubTab === 'blogs' && (
                  <>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-sm)',
                        marginBottom: 'var(--spacing-md)',
                      }}
                    >
                      <BookOpen size={18} color="var(--color-primary)" />
                      <h2
                        style={{
                          fontFamily: 'var(--font-display)',
                          fontSize: 20,
                          fontWeight: 400,
                          letterSpacing: '-0.3px',
                          color: 'var(--color-ink)',
                          margin: 0,
                        }}
                      >
                        收藏的博客文章
                      </h2>
                    </div>
                    {favoriteBlogs.length === 0 ? (
                      <p style={{ fontSize: 14, color: 'var(--color-muted)', margin: 0, textAlign: 'center', padding: 'var(--spacing-lg)' }}>
                        暂无收藏的文章
                      </p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
                        {favoriteBlogs.map((blog) => (
                          <div
                            key={blog.id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '12px 16px',
                              borderRadius: 'var(--rounded-md)',
                              backgroundColor: 'var(--color-canvas)',
                            }}
                          >
                            <div style={{ minWidth: 0, flex: 1 }}>
                              <div
                                style={{
                                  fontSize: 14,
                                  fontWeight: 500,
                                  color: 'var(--color-body-strong)',
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                }}
                              >
                                {blog.title}
                              </div>
                              <div style={{ fontSize: 12, color: 'var(--color-muted-soft)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span
                                  style={{
                                    padding: '2px 8px',
                                    borderRadius: 'var(--rounded-pill)',
                                    backgroundColor: 'var(--color-surface-soft)',
                                    fontSize: 11,
                                    fontWeight: 500,
                                    color: 'var(--color-muted)',
                                  }}
                                >
                                  {blog.category.name}
                                </span>
                                <span>{formatDateCN(blog.created_at)}</span>
                              </div>
                            </div>
                            <button
                              onClick={() => handleUnfavoriteBlog(blog.id)}
                              style={{
                                width: 32,
                                height: 32,
                                borderRadius: 'var(--rounded-full)',
                                backgroundColor: 'transparent',
                                border: '1px solid var(--color-hairline)',
                                color: 'var(--color-muted)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                                transition: 'all 150ms ease',
                                flexShrink: 0,
                                marginLeft: 'var(--spacing-sm)',
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = 'var(--color-error)'
                                e.currentTarget.style.color = '#fff'
                                e.currentTarget.style.borderColor = 'var(--color-error)'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'transparent'
                                e.currentTarget.style.color = 'var(--color-muted)'
                                e.currentTarget.style.borderColor = 'var(--color-hairline)'
                              }}
                              title="取消收藏"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
