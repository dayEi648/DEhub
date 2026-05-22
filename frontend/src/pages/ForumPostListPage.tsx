import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  MessageSquare,
  User,
  Eye,
  MessageCircle,
  Clock,
  ArrowLeft,
  Flame,
  CalendarClock,
  Plus,
  Send,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { getForumPostList, getForumZoneBySlug, createForumPost } from '../api/forum'
import { followZone, unfollowZone, getFollowedZones } from '../api/favorites'
import AppTopNav from '../components/AppTopNav'
import Footer from '../components/Footer'
import Pagination from '../components/Pagination'
import { useLogout } from '../hooks/useLogout'
import { formatDate } from '../utils/format'
import type { ForumPost, ForumZone } from '../types/forum'

const PAGE_SIZE = 15

/* ─── Create Post Modal ─── */
function CreatePostModal({
  zoneId,
  onClose,
  onSuccess,
}: {
  zoneId: number
  onClose: () => void
  onSuccess: () => void
}) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) return
    setSubmitting(true)
    try {
      await createForumPost({
        title: title.trim(),
        content: content.trim(),
        zone_id: zoneId,
      })
      onSuccess()
      onClose()
    } catch {
      toast.error('发帖失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        backgroundColor: 'rgba(20,20,19,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-xl)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: 'var(--rounded-lg)',
          padding: 'var(--spacing-xl)',
          width: '100%',
          maxWidth: 560,
          maxHeight: '90vh',
          overflow: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--spacing-lg)' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 400, margin: 0, color: 'var(--color-ink)' }}>
            发表新帖
          </h3>
          <button
            onClick={onClose}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-full)',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-muted)',
            }}
          >
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-body-strong)', marginBottom: 'var(--spacing-xs)' }}>
              标题
            </label>
            <input
              type="text"
              placeholder="请输入帖子标题..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                width: '100%',
                height: 44,
                padding: '0 var(--spacing-md)',
                borderRadius: 'var(--rounded-md)',
                border: '1px solid var(--color-hairline)',
                backgroundColor: 'var(--color-surface-soft)',
                fontSize: 15,
                color: 'var(--color-ink)',
                outline: 'none',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-body-strong)', marginBottom: 'var(--spacing-xs)' }}>
              内容
            </label>
            <textarea
              placeholder="请输入帖子内容..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              style={{
                width: '100%',
                minHeight: 160,
                padding: 'var(--spacing-md)',
                borderRadius: 'var(--rounded-md)',
                border: '1px solid var(--color-hairline)',
                backgroundColor: 'var(--color-surface-soft)',
                fontSize: 15,
                lineHeight: 1.6,
                color: 'var(--color-ink)',
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'var(--font-body)',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
            <button
              onClick={onClose}
              style={{
                padding: '10px 20px',
                backgroundColor: 'transparent',
                color: 'var(--color-muted)',
                borderRadius: 'var(--rounded-md)',
                fontSize: 14,
                fontWeight: 500,
                border: '1px solid var(--color-hairline)',
                cursor: 'pointer',
              }}
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting || !title.trim() || !content.trim()}
              style={{
                padding: '10px 20px',
                backgroundColor: !title.trim() || !content.trim() ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
                color: !title.trim() || !content.trim() ? 'var(--color-muted)' : 'var(--color-on-primary)',
                borderRadius: 'var(--rounded-md)',
                fontSize: 14,
                fontWeight: 500,
                border: 'none',
                cursor: !title.trim() || !content.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Send size={14} />
              {submitting ? '发表中...' : '发表'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Post Card ─── */
function PostCard({ post }: { post: ForumPost }) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/forums/p/${post.id}`)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-md)',
        padding: 'var(--spacing-md) var(--spacing-lg)',
        borderRadius: 'var(--rounded-md)',
        cursor: 'pointer',
        transition: 'background-color 150ms ease',
        borderBottom: '1px solid var(--color-hairline-soft)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent'
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 'var(--rounded-full)',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-primary)',
          flexShrink: 0,
          overflow: 'hidden',
        }}
      >
        {post.user.avatar_url ? (
          <img src={post.user.avatar_url} alt={post.user.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
          <User size={18} />
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: 15,
            fontWeight: 500,
            color: 'var(--color-body-strong)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            marginBottom: 4,
          }}
        >
          {post.title}
        </div>
        <div
          style={{
            fontSize: 13,
            color: 'var(--color-muted-soft)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-sm)',
            flexWrap: 'wrap',
          }}
        >
          <span>{post.user.username}</span>
          <span>·</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Clock size={12} />
            {formatDate(post.created_at)}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', flexShrink: 0, fontSize: 13, color: 'var(--color-muted-soft)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <Eye size={14} />
          {post.view_count}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <MessageCircle size={14} />
          {post.reply_count}
        </span>
      </div>
    </div>
  )
}

/* ─── Main Page ─── */
export default function ForumPostListPage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [zone, setZone] = useState<ForumZone | null>(null)
  const [posts, setPosts] = useState<ForumPost[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<'created' | 'view'>('created')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [isFollowed, setIsFollowed] = useState(false)
  const [following, setFollowing] = useState(false)

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const fetchZone = useCallback(async () => {
    if (!slug) return
    try {
      const [zoneRes, followRes] = await Promise.all([
        getForumZoneBySlug(slug),
        getFollowedZones({ limit: 100 }),
      ])
      setZone(zoneRes.data)
      setIsFollowed(followRes.data.items.some((item) => item.id === zoneRes.data.id))
    } catch {
      setError('分区不存在')
    }
  }, [slug])

  const fetchPosts = useCallback(async () => {
    if (!zone) return
    setLoading(true)
    setError('')
    try {
      const res = await getForumPostList({
        zone_id: zone.id,
        sort_by: sortBy,
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      })
      setPosts(res.data.items)
      setTotal(res.data.total)
    } catch {
      setError('加载帖子失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [zone, sortBy, page])

  useEffect(() => {
    fetchZone()
  }, [fetchZone])

  useEffect(() => {
    fetchPosts()
  }, [fetchPosts])

  const handleLogout = useLogout()

  if (error && !zone) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
        <AppTopNav onLogout={handleLogout} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--color-muted)', gap: 'var(--spacing-md)' }}>
          <MessageSquare size={48} style={{ opacity: 0.3 }} />
          <p style={{ fontSize: 16, margin: 0 }}>{error}</p>
          <button
            onClick={() => navigate('/forums')}
            style={{
              padding: '10px var(--spacing-lg)',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <ArrowLeft size={14} />
            返回论坛首页
          </button>
        </div>
        <Footer />
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      <AppTopNav onLogout={handleLogout} />

      {/* Zone Header */}
      <section
        style={{
          backgroundColor: 'var(--color-surface-soft)',
          padding: 'var(--spacing-section) var(--spacing-xl) var(--spacing-xl)',
        }}
      >
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <button
            onClick={() => navigate('/forums')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 14,
              fontWeight: 500,
              color: 'var(--color-muted)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              marginBottom: 'var(--spacing-lg)',
              transition: 'color 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-primary)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-muted)'
            }}
          >
            <ArrowLeft size={14} />
            返回论坛首页
          </button>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '4px 12px',
              borderRadius: 'var(--rounded-pill)',
              backgroundColor: 'var(--color-canvas)',
              fontSize: 12,
              fontWeight: 500,
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
              color: 'var(--color-primary)',
              marginBottom: 'var(--spacing-md)',
            }}
          >
            <MessageSquare size={12} />
            {zone?.zone_name || '论坛分区'}
          </div>

          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(28px, 4vw, 48px)',
              fontWeight: 400,
              lineHeight: 1.1,
              letterSpacing: '-1px',
              color: 'var(--color-ink)',
              margin: '0 0 var(--spacing-sm)',
            }}
          >
            {zone?.zone_name || '加载中...'}
          </h1>

          <p style={{ fontSize: 16, lineHeight: 1.55, color: 'var(--color-muted)', margin: 0, maxWidth: 560 }}>
            {zone?.description || ' '}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)', marginTop: 'var(--spacing-md)', fontSize: 14, color: 'var(--color-muted-soft)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Eye size={14} />
              {zone?.view_count ?? 0} 浏览
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <User size={14} />
              区主：{zone?.manager.username || '-'}
            </span>
            {zone && (
              <button
                onClick={async () => {
                  if (following) return
                  setFollowing(true)
                  try {
                    if (isFollowed) {
                      await unfollowZone(zone.id)
                      setIsFollowed(false)
                    } else {
                      await followZone(zone.id)
                      setIsFollowed(true)
                    }
                  } catch {
                    toast.error(isFollowed ? '取消关注失败' : '关注失败')
                  } finally {
                    setFollowing(false)
                  }
                }}
                disabled={following}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  fontSize: 14,
                  fontWeight: 500,
                  color: isFollowed ? 'var(--color-primary)' : 'var(--color-muted-soft)',
                  background: 'transparent',
                  border: 'none',
                  cursor: following ? 'not-allowed' : 'pointer',
                  padding: 0,
                }}
              >
                <Plus size={14} />
                {isFollowed ? '已关注' : '关注'}
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Post List */}
      <section style={{ flex: 1, padding: 'var(--spacing-xl) var(--spacing-xl)', backgroundColor: 'var(--color-canvas)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* Toolbar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 'var(--spacing-lg)',
              flexWrap: 'wrap',
              gap: 'var(--spacing-sm)',
            }}
          >
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
              <button
                onClick={() => {
                  setSortBy('created')
                  setPage(1)
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: 'var(--rounded-md)',
                  fontSize: 14,
                  fontWeight: 500,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 150ms ease',
                  backgroundColor: sortBy === 'created' ? 'var(--color-surface-card)' : 'transparent',
                  color: sortBy === 'created' ? 'var(--color-ink)' : 'var(--color-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <CalendarClock size={14} />
                最新
              </button>
              <button
                onClick={() => {
                  setSortBy('view')
                  setPage(1)
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: 'var(--rounded-md)',
                  fontSize: 14,
                  fontWeight: 500,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 150ms ease',
                  backgroundColor: sortBy === 'view' ? 'var(--color-surface-card)' : 'transparent',
                  color: sortBy === 'view' ? 'var(--color-ink)' : 'var(--color-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <Flame size={14} />
                最热
              </button>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              style={{
                padding: '10px 20px',
                backgroundColor: 'var(--color-primary)',
                color: 'var(--color-on-primary)',
                borderRadius: 'var(--rounded-md)',
                fontSize: 14,
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                transition: 'background-color 150ms ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-primary)'
              }}
            >
              <Plus size={14} />
              发表新帖
            </button>
          </div>

          {/* List */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-muted)' }}>
              加载中...
            </div>
          ) : posts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-muted)' }}>
              <MessageSquare size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.3 }} />
              <p style={{ fontSize: 16, margin: 0 }}>暂无帖子</p>
              <p style={{ fontSize: 14, color: 'var(--color-muted-soft)', marginTop: 'var(--spacing-xs)' }}>
                快来发表第一篇帖子吧
              </p>
            </div>
          ) : (
            <div
              style={{
                backgroundColor: 'var(--color-surface-card)',
                borderRadius: 'var(--rounded-lg)',
                overflow: 'hidden',
              }}
            >
              {posts.map((post) => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}

          <Pagination current={page} total={totalPages} onChange={setPage} />
        </div>
      </section>

      <Footer />

      {showCreateModal && zone && (
        <CreatePostModal
          zoneId={zone.id}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setPage(1)
            setSortBy('created')
            fetchPosts()
          }}
        />
      )}
    </div>
  )
}
