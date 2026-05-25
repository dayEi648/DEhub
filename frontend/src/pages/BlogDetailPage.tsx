import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  BookOpen,
  Eye,
  MessageCircle,
  Clock,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  User,
  ChevronLeft,
  Send,
  Heart,
  Trash2,
  Flame,
  CalendarClock,
  ChevronDown,
  ChevronUp,
  Edit3,
  Plus,
  Minus,
} from 'lucide-react'
import {
  getBlogPostBySlug,
  getBlogCategories,
  updateBlogPost,
  deleteBlogPost,
  publishBlogPost,
  unpublishBlogPost,
} from '../api/blog'
import { getUser } from '../utils/auth'
import BlogEditorModal from '../components/BlogEditorModal'
import { getCommentList, createComment, deleteComment, likeComment, unlikeComment } from '../api/comments'
import { favoriteBlogPost, unfavoriteBlogPost, getBlogPostFavoriteStatus } from '../api/favorites'
import { toast } from 'sonner'
import AppTopNav from '../components/AppTopNav'
import { useLogout } from '../hooks/useLogout'
import { formatDate, formatDateTime } from '../utils/format'
import type { BlogPostDetailResponse, BlogPostListItem, BlogCategoryWithPostCount } from '../types/blog'
import type { CommentResponse } from '../types/comments'

/* ─── Markdown Renderer ─── */
function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 32,
                fontWeight: 400,
                lineHeight: 1.15,
                letterSpacing: '-0.5px',
                color: 'var(--color-ink)',
                margin: 'var(--spacing-xl) 0 var(--spacing-md)',
                paddingBottom: 'var(--spacing-sm)',
                borderBottom: '1px solid var(--color-hairline-soft)',
              }}
            >
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 26,
                fontWeight: 400,
                lineHeight: 1.2,
                letterSpacing: '-0.3px',
                color: 'var(--color-ink)',
                margin: 'var(--spacing-xl) 0 var(--spacing-md)',
                paddingBottom: 'var(--spacing-sm)',
                borderBottom: '1px solid var(--color-hairline-soft)',
              }}
            >
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 22,
                fontWeight: 400,
                lineHeight: 1.2,
                letterSpacing: '-0.3px',
                color: 'var(--color-ink)',
                margin: 'var(--spacing-lg) 0 var(--spacing-sm)',
              }}
            >
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p
              style={{
                fontSize: 16,
                lineHeight: 1.75,
                color: 'var(--color-body)',
                margin: '0 0 var(--spacing-md)',
              }}
            >
              {children}
            </p>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              style={{
                color: 'var(--color-primary)',
                textDecoration: 'none',
                borderBottom: '1px solid var(--color-primary)',
                transition: 'opacity 150ms ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.8'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1'
              }}
            >
              {children}
            </a>
          ),
          ul: ({ children }) => (
            <ul
              style={{
                fontSize: 16,
                lineHeight: 1.75,
                color: 'var(--color-body)',
                margin: '0 0 var(--spacing-md)',
                paddingLeft: 'var(--spacing-xl)',
              }}
            >
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol
              style={{
                fontSize: 16,
                lineHeight: 1.75,
                color: 'var(--color-body)',
                margin: '0 0 var(--spacing-md)',
                paddingLeft: 'var(--spacing-xl)',
              }}
            >
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li style={{ marginBottom: 'var(--spacing-xs)' }}>{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote
              style={{
                margin: 'var(--spacing-md) 0',
                padding: 'var(--spacing-md) var(--spacing-lg)',
                borderLeft: '3px solid var(--color-primary)',
                backgroundColor: 'var(--color-surface-soft)',
                borderRadius: '0 var(--rounded-sm) var(--rounded-sm) 0',
                color: 'var(--color-body-strong)',
                fontStyle: 'italic',
              }}
            >
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const isInline = !className
            if (isInline) {
              return (
                <code
                  style={{
                    fontFamily: 'var(--font-code)',
                    fontSize: 14,
                    backgroundColor: 'var(--color-surface-soft)',
                    padding: '2px 6px',
                    borderRadius: 'var(--rounded-xs)',
                    color: 'var(--color-primary-active)',
                  }}
                >
                  {children}
                </code>
              )
            }
            return (
              <pre
                style={{
                  backgroundColor: 'var(--color-surface-dark)',
                  color: 'var(--color-on-dark)',
                  padding: 'var(--spacing-lg)',
                  borderRadius: 'var(--rounded-lg)',
                  overflowX: 'auto',
                  fontFamily: 'var(--font-code)',
                  fontSize: 14,
                  lineHeight: 1.6,
                  margin: 'var(--spacing-md) 0',
                }}
              >
                <code>{children}</code>
              </pre>
            )
          },
          hr: () => (
            <hr
              style={{
                border: 'none',
                borderTop: '1px solid var(--color-hairline-soft)',
                margin: 'var(--spacing-xl) 0',
              }}
            />
          ),
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              style={{
                maxWidth: '100%',
                borderRadius: 'var(--rounded-lg)',
                margin: 'var(--spacing-md) 0',
              }}
            />
          ),
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', margin: 'var(--spacing-md) 0' }}>
              <table
                style={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              >
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th
              style={{
                padding: 'var(--spacing-sm) var(--spacing-md)',
                backgroundColor: 'var(--color-surface-soft)',
                borderBottom: '2px solid var(--color-hairline)',
                textAlign: 'left',
                fontWeight: 600,
                color: 'var(--color-ink)',
              }}
            >
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td
              style={{
                padding: 'var(--spacing-sm) var(--spacing-md)',
                borderBottom: '1px solid var(--color-hairline-soft)',
                color: 'var(--color-body)',
              }}
            >
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

/* ─── Post Navigation ─── */
function PostNavigation({
  prev,
  next,
}: {
  prev: BlogPostListItem | null
  next: BlogPostListItem | null
}) {
  const navigate = useNavigate()
  if (!prev && !next) return null

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 'var(--spacing-lg)',
        marginTop: 'var(--spacing-xl)',
      }}
    >
      {prev ? (
        <button
          onClick={() => navigate(`/blogs/${prev.slug}`)}
          style={{
            textAlign: 'left',
            padding: 'var(--spacing-lg)',
            backgroundColor: 'var(--color-surface-card)',
            borderRadius: 'var(--rounded-lg)',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 150ms ease',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-xs)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-cream-strong)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-card)'
          }}
        >
          <span
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: 'var(--color-muted-soft)',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <ArrowLeft size={12} />
            上一篇
          </span>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 18,
              fontWeight: 400,
              color: 'var(--color-ink)',
              lineHeight: 1.3,
            }}
          >
            {prev.title}
          </span>
        </button>
      ) : (
        <div />
      )}

      {next ? (
        <button
          onClick={() => navigate(`/blogs/${next.slug}`)}
          style={{
            textAlign: 'right',
            padding: 'var(--spacing-lg)',
            backgroundColor: 'var(--color-surface-card)',
            borderRadius: 'var(--rounded-lg)',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 150ms ease',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-xs)',
            alignItems: 'flex-end',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-cream-strong)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-card)'
          }}
        >
          <span
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: 'var(--color-muted-soft)',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            下一篇
            <ArrowRight size={12} />
          </span>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 18,
              fontWeight: 400,
              color: 'var(--color-ink)',
              lineHeight: 1.3,
            }}
          >
            {next.title}
          </span>
        </button>
      ) : (
        <div />
      )}
    </div>
  )
}

/* ─── Nested Reply Input ─── */
function ReplyInput({
  placeholder,
  onSubmit,
  onCancel,
  submitText = '回复',
}: {
  placeholder: string
  onSubmit: (content: string) => void
  onCancel?: () => void
  submitText?: string
}) {
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!value.trim()) return
    setSubmitting(true)
    await onSubmit(value.trim())
    setSubmitting(false)
    setValue('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
      <textarea
        placeholder={placeholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={{
          width: '100%',
          minHeight: 60,
          padding: 'var(--spacing-sm)',
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          fontSize: 14,
          lineHeight: 1.6,
          color: 'var(--color-ink)',
          resize: 'vertical',
          outline: 'none',
          fontFamily: 'var(--font-body)',
        }}
      />
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--spacing-sm)' }}>
        {onCancel && (
          <button
            onClick={onCancel}
            style={{
              padding: '8px 16px',
              backgroundColor: 'transparent',
              color: 'var(--color-muted)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 13,
              fontWeight: 500,
              border: '1px solid var(--color-hairline)',
              cursor: 'pointer',
            }}
          >
            取消
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={submitting || !value.trim()}
          style={{
            padding: '8px 16px',
            backgroundColor: !value.trim() ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
            color: !value.trim() ? 'var(--color-muted)' : 'var(--color-on-primary)',
            borderRadius: 'var(--rounded-md)',
            fontSize: 13,
            fontWeight: 500,
            border: 'none',
            cursor: !value.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <Send size={12} />
          {submitting ? '发送中...' : submitText}
        </button>
      </div>
    </div>
  )
}

/* ─── Inner Reply Item (普通回复 + 嵌套回复同一级) ─── */
function InnerReplyItem({
  comment,
  currentUserId,
  isAdmin,
  onLike,
  onUnlike,
  onDelete,
  onReply,
}: {
  comment: CommentResponse
  currentUserId: number | null
  isAdmin: boolean
  onLike: (id: number) => void
  onUnlike: (id: number) => void
  onDelete: (id: number) => void
  onReply: (nestedParentId: number, username: string, content: string) => void
}) {
  const canDelete = currentUserId === comment.user_id || isAdmin
  const [showReplyInput, setShowReplyInput] = useState(false)

  return (
    <div style={{ padding: 'var(--spacing-sm) 0', borderBottom: '1px solid var(--color-hairline-soft)' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--spacing-sm)' }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 'var(--rounded-full)',
            backgroundColor: 'var(--color-surface-card)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-primary)',
            flexShrink: 0,
            overflow: 'hidden',
            fontSize: 12,
          }}
        >
          {comment.user.avatar_url ? (
            <img src={comment.user.avatar_url} alt={comment.user.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <User size={12} />
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-xs)', marginBottom: 2, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-body-strong)' }}>
              {comment.user.username}
            </span>
            <span style={{ fontSize: 11, color: 'var(--color-muted-soft)' }}>
              {formatDateTime(comment.created_at)}
            </span>
          </div>

          <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-body)', margin: '0 0 var(--spacing-xs)' }}>
            {comment.content}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <button
              onClick={() => (comment.is_liked ? onUnlike(comment.id) : onLike(comment.id))}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 3,
                fontSize: 12,
                fontWeight: 500,
                color: comment.is_liked ? 'var(--color-primary)' : 'var(--color-muted-soft)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              <Heart size={12} fill={comment.is_liked ? 'var(--color-primary)' : 'none'} />
              {comment.likecount}
            </button>

            <button
              onClick={() => setShowReplyInput((s) => !s)}
              style={{
                fontSize: 12,
                fontWeight: 500,
                color: 'var(--color-muted-soft)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              回复
            </button>

            {canDelete && (
              <button
                onClick={() => {
                  if (window.confirm('确定要删除这条评论吗？')) {
                    onDelete(comment.id)
                  }
                }}
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-muted-soft)',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--color-error)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--color-muted-soft)'
                }}
              >
                删除
              </button>
            )}
          </div>

          {showReplyInput && (
            <ReplyInput
              placeholder={`回复 @${comment.user.username}：`}
              onSubmit={(content) => {
                onReply(comment.id, comment.user.username, content)
                setShowReplyInput(false)
              }}
              onCancel={() => setShowReplyInput(false)}
              submitText="回复"
            />
          )}
        </div>
      </div>
    </div>
  )
}

/* ─── Surface Comment Item ─── */
function SurfaceCommentItem({
  comment,
  currentUserId,
  isAdmin,
  onLike,
  onUnlike,
  onDelete,
  postId,
}: {
  comment: CommentResponse
  currentUserId: number | null
  isAdmin: boolean
  onLike: (id: number) => void
  onUnlike: (id: number) => void
  onDelete: (id: number) => void
  postId: number
}) {
  const canDelete = currentUserId === comment.user_id || isAdmin
  const [showReplies, setShowReplies] = useState(false)
  const [replies, setReplies] = useState<CommentResponse[]>([])
  const [replyTotal, setReplyTotal] = useState(0)
  const [replyLoading, setReplyLoading] = useState(false)
  const [showReplyInput, setShowReplyInput] = useState(false)
  const [replyPage, setReplyPage] = useState(1)

  const REPLY_PAGE_SIZE = 5
  const replyTotalPages = Math.ceil(replyTotal / REPLY_PAGE_SIZE)

  const fetchReplies = useCallback(async () => {
    setReplyLoading(true)
    try {
      const res = await getCommentList({
        target_type: 'blog_post',
        target_id: postId,
        parent_id: comment.id,
        sort_by: 'time',
        skip: (replyPage - 1) * REPLY_PAGE_SIZE,
        limit: REPLY_PAGE_SIZE,
      })
      setReplies(res.data.items)
      setReplyTotal(res.data.total)
    } catch {
      // ignore
    } finally {
      setReplyLoading(false)
    }
  }, [postId, comment.id, replyPage])

  useEffect(() => {
    if (showReplies) {
      fetchReplies()
    }
  }, [showReplies, fetchReplies])

  const handleReplyToInner = async (nestedParentId: number, username: string, rawContent: string) => {
    try {
      const content = `@${username}：${rawContent}`
      await createComment({
        target_type: 'blog_post',
        target_id: postId,
        parent_id: comment.id,
        is_nested: true,
        nested_parent_id: nestedParentId,
        content,
      })
      fetchReplies()
    } catch {
      toast.error('回复失败')
    }
  }

  const handleReplyToSurface = async (content: string) => {
    try {
      await createComment({
        target_type: 'blog_post',
        target_id: postId,
        parent_id: comment.id,
        content,
      })
      setShowReplyInput(false)
      if (showReplies) {
        fetchReplies()
      } else {
        setShowReplies(true)
      }
    } catch {
      toast.error('回复失败')
    }
  }

  return (
    <div
      style={{
        padding: 'var(--spacing-md) 0',
        borderBottom: '1px solid var(--color-hairline)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--spacing-md)' }}>
        {/* Avatar */}
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 'var(--rounded-full)',
            backgroundColor: 'var(--color-surface-card)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-primary)',
            flexShrink: 0,
            overflow: 'hidden',
          }}
        >
          {comment.user.avatar_url ? (
            <img src={comment.user.avatar_url} alt={comment.user.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <User size={18} />
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-body-strong)' }}>
              {comment.user.username}
            </span>
            <span style={{ fontSize: 12, color: 'var(--color-muted-soft)' }}>
              {formatDateTime(comment.created_at)}
            </span>
          </div>

          <p style={{ fontSize: 15, lineHeight: 1.7, color: 'var(--color-body)', margin: '0 0 var(--spacing-sm)' }}>
            {comment.content}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
            <button
              onClick={() => (comment.is_liked ? onUnlike(comment.id) : onLike(comment.id))}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 13,
                fontWeight: 500,
                color: comment.is_liked ? 'var(--color-primary)' : 'var(--color-muted-soft)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              <Heart size={14} fill={comment.is_liked ? 'var(--color-primary)' : 'none'} />
              {comment.likecount}
            </button>

            <button
              onClick={() => setShowReplyInput((s) => !s)}
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--color-muted-soft)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              回复
            </button>

            <button
              onClick={() => setShowReplies((s) => !s)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 3,
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--color-primary)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              {showReplies ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {replyTotal > 0 ? `${replyTotal} 条回复` : '查看回复'}
            </button>

            {canDelete && (
              <button
                onClick={() => {
                  if (window.confirm('确定要删除这条评论吗？')) {
                    onDelete(comment.id)
                  }
                }}
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: 'var(--color-muted-soft)',
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--color-error)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--color-muted-soft)'
                }}
              >
                <Trash2 size={14} />
                删除
              </button>
            )}
          </div>

          {/* Reply input for surface comment */}
          {showReplyInput && (
            <div style={{ marginTop: 'var(--spacing-sm)', paddingLeft: 0 }}>
              <ReplyInput
                placeholder="写下你的回复..."
                onSubmit={handleReplyToSurface}
                onCancel={() => setShowReplyInput(false)}
                submitText="回复"
              />
            </div>
          )}

          {/* Inner replies */}
          {showReplies && (
            <div
              style={{
                marginTop: 'var(--spacing-md)',
                paddingLeft: 'var(--spacing-md)',
                borderLeft: '2px solid var(--color-hairline-soft)',
              }}
            >
              {replyLoading ? (
                <div style={{ padding: 'var(--spacing-sm) 0', fontSize: 13, color: 'var(--color-muted)' }}>
                  加载回复中...
                </div>
              ) : replies.length === 0 ? (
                <div style={{ padding: 'var(--spacing-sm) 0', fontSize: 13, color: 'var(--color-muted)' }}>
                  暂无回复
                </div>
              ) : (
                <>
                  {replies.map((reply) => (
                    <InnerReplyItem
                      key={reply.id}
                      comment={reply}
                      currentUserId={currentUserId}
                      isAdmin={isAdmin}
                      onLike={onLike}
                      onUnlike={onUnlike}
                      onDelete={onDelete}
                      onReply={(nestedParentId, username, content) => {
                        const rawContent = content || prompt(`回复 @${username}：`)
                        if (rawContent && rawContent.trim()) {
                          handleReplyToInner(nestedParentId, username, rawContent.trim())
                        }
                      }}
                    />
                  ))}
                  {replyTotalPages > 1 && (
                    <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-xs)', padding: 'var(--spacing-sm) 0' }}>
                      <button
                        onClick={() => setReplyPage((p) => Math.max(1, p - 1))}
                        disabled={replyPage === 1}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 'var(--rounded-md)',
                          border: '1px solid var(--color-hairline)',
                          backgroundColor: 'var(--color-canvas)',
                          cursor: replyPage === 1 ? 'not-allowed' : 'pointer',
                          opacity: replyPage === 1 ? 0.5 : 1,
                          color: 'var(--color-ink)',
                          fontSize: 12,
                        }}
                      >
                        <ChevronLeft size={12} />
                      </button>
                      <span style={{ display: 'flex', alignItems: 'center', padding: '0 var(--spacing-sm)', fontSize: 13, color: 'var(--color-muted)' }}>
                        {replyPage} / {replyTotalPages}
                      </span>
                      <button
                        onClick={() => setReplyPage((p) => Math.min(replyTotalPages, p + 1))}
                        disabled={replyPage === replyTotalPages}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 'var(--rounded-md)',
                          border: '1px solid var(--color-hairline)',
                          backgroundColor: 'var(--color-canvas)',
                          cursor: replyPage === replyTotalPages ? 'not-allowed' : 'pointer',
                          opacity: replyPage === replyTotalPages ? 0.5 : 1,
                          color: 'var(--color-ink)',
                          fontSize: 12,
                        }}
                      >
                        <ChevronLeft size={12} style={{ transform: 'rotate(180deg)' }} />
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ─── Comment Section ─── */
function CommentSection({ postId, totalCommentCount }: { postId: number; totalCommentCount: number }) {
  const currentUser = getUser()
  const [comments, setComments] = useState<CommentResponse[]>([])
  const [total, setTotal] = useState(0)
  const [sortBy, setSortBy] = useState<'time' | 'hot'>('time')
  const [page, setPage] = useState(1)
  const [newComment, setNewComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const PAGE_SIZE = 10
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const fetchComments = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getCommentList({
        target_type: 'blog_post',
        target_id: postId,
        parent_id: 0,
        sort_by: sortBy,
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      })
      setComments(res.data.items)
      setTotal(res.data.total)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [postId, sortBy, page])

  useEffect(() => {
    fetchComments()
  }, [fetchComments])

  const handleSubmit = async () => {
    if (!newComment.trim()) return
    setSubmitting(true)
    try {
      await createComment({
        target_type: 'blog_post',
        target_id: postId,
        content: newComment.trim(),
      })
      setNewComment('')
      setPage(1)
      setSortBy('time')
      fetchComments()
    } catch {
      toast.error('评论发表失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleLike = async (commentId: number) => {
    try {
      await likeComment(commentId)
      setComments((prev) =>
        prev.map((c) => (c.id === commentId ? { ...c, is_liked: true, likecount: c.likecount + 1 } : c))
      )
    } catch {
      // ignore
    }
  }

  const handleUnlike = async (commentId: number) => {
    try {
      await unlikeComment(commentId)
      setComments((prev) =>
        prev.map((c) => (c.id === commentId ? { ...c, is_liked: false, likecount: c.likecount - 1 } : c))
      )
    } catch {
      // ignore
    }
  }

  const handleDelete = async (commentId: number) => {
    try {
      await deleteComment(commentId)
      fetchComments()
    } catch {
      toast.error('删除失败')
    }
  }

  return (
    <section style={{ marginTop: 'var(--spacing-section)' }}>
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
        <h2
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 400,
            lineHeight: 1.2,
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-sm)',
          }}
        >
          <MessageCircle size={24} />
          评论
          <span style={{ fontSize: 16, color: 'var(--color-muted-soft)', fontFamily: 'var(--font-body)' }}>
            ({totalCommentCount})
          </span>
        </h2>

        <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
          <button
            onClick={() => {
              setSortBy('time')
              setPage(1)
            }}
            style={{
              padding: '6px 12px',
              borderRadius: 'var(--rounded-md)',
              fontSize: 13,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              backgroundColor: sortBy === 'time' ? 'var(--color-surface-card)' : 'transparent',
              color: sortBy === 'time' ? 'var(--color-ink)' : 'var(--color-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <CalendarClock size={13} />
            最新
          </button>
          <button
            onClick={() => {
              setSortBy('hot')
              setPage(1)
            }}
            style={{
              padding: '6px 12px',
              borderRadius: 'var(--rounded-md)',
              fontSize: 13,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              backgroundColor: sortBy === 'hot' ? 'var(--color-surface-card)' : 'transparent',
              color: sortBy === 'hot' ? 'var(--color-ink)' : 'var(--color-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Flame size={13} />
            最热
          </button>
        </div>
      </div>

      {/* Input */}
      <div
        style={{
          backgroundColor: 'var(--color-surface-card)',
          borderRadius: 'var(--rounded-lg)',
          padding: 'var(--spacing-lg)',
          marginBottom: 'var(--spacing-lg)',
        }}
      >
        <textarea
          placeholder={currentUser ? '写下你的评论...' : '请先登录后评论'}
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          disabled={!currentUser || submitting}
          style={{
            width: '100%',
            minHeight: 80,
            padding: 'var(--spacing-md)',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            fontSize: 15,
            lineHeight: 1.6,
            color: 'var(--color-ink)',
            resize: 'vertical',
            outline: 'none',
            fontFamily: 'var(--font-body)',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--spacing-sm)' }}>
          <button
            onClick={handleSubmit}
            disabled={!currentUser || submitting || !newComment.trim()}
            style={{
              padding: '10px var(--spacing-lg)',
              backgroundColor: !currentUser || !newComment.trim() ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
              color: !currentUser || !newComment.trim() ? 'var(--color-muted)' : 'var(--color-on-primary)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: !currentUser || !newComment.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              transition: 'background-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              if (currentUser && newComment.trim()) {
                e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
              }
            }}
            onMouseLeave={(e) => {
              if (currentUser && newComment.trim()) {
                e.currentTarget.style.backgroundColor = 'var(--color-primary)'
              }
            }}
          >
            <Send size={14} />
            {submitting ? '发表中...' : '发表评论'}
          </button>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--spacing-xl) 0', color: 'var(--color-muted)' }}>加载评论中...</div>
      ) : comments.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 'var(--spacing-xl) 0', color: 'var(--color-muted)' }}>
          <MessageCircle size={36} style={{ marginBottom: 'var(--spacing-sm)', opacity: 0.3 }} />
          <p style={{ fontSize: 14, margin: 0 }}>暂无评论，快来抢沙发吧</p>
        </div>
      ) : (
        <div>
          {comments.map((comment) => (
            <SurfaceCommentItem
              key={comment.id}
              comment={comment}
              currentUserId={currentUser?.id ?? null}
              isAdmin={(currentUser?.permission ?? 0) >= 1}
              onLike={handleLike}
              onUnlike={handleUnlike}
              onDelete={handleDelete}
              postId={postId}
            />
          ))}

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-xs)', marginTop: 'var(--spacing-lg)' }}>
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--rounded-md)',
                  border: '1px solid var(--color-hairline)',
                  backgroundColor: 'var(--color-canvas)',
                  cursor: page === 1 ? 'not-allowed' : 'pointer',
                  opacity: page === 1 ? 0.5 : 1,
                  color: 'var(--color-ink)',
                  fontSize: 13,
                }}
              >
                <ChevronLeft size={14} />
              </button>
              <span style={{ display: 'flex', alignItems: 'center', padding: '0 var(--spacing-sm)', fontSize: 14, color: 'var(--color-muted)' }}>
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--rounded-md)',
                  border: '1px solid var(--color-hairline)',
                  backgroundColor: 'var(--color-canvas)',
                  cursor: page === totalPages ? 'not-allowed' : 'pointer',
                  opacity: page === totalPages ? 0.5 : 1,
                  color: 'var(--color-ink)',
                  fontSize: 13,
                }}
              >
                <ChevronLeft size={14} style={{ transform: 'rotate(180deg)' }} />
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

/* ─── Footer ─── */
function Footer() {
  return (
    <footer
      style={{
        backgroundColor: 'var(--color-surface-dark)',
        color: 'var(--color-on-dark-soft)',
        padding: 'var(--spacing-xl) var(--spacing-xl)',
        marginTop: 'auto',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <Sparkles size={16} color="var(--color-on-dark)" />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, color: 'var(--color-on-dark)' }}>DE hub</span>
        </div>
        <span style={{ fontSize: 13, color: 'var(--color-on-dark-soft)' }}>
          © {new Date().getFullYear()} Developer Space. All rights reserved.
        </span>
      </div>
    </footer>
  )
}

/* ─── Main Page ─── */
export default function BlogDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<BlogPostDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriting, setFavoriting] = useState(false)
  const [showEditor, setShowEditor] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [categories, setCategories] = useState<BlogCategoryWithPostCount[]>([])
  const currentUser = getUser()
  const isSuperAdmin = currentUser?.permission === 2
  const currentUserId = currentUser?.id ?? null

  const fetchPost = useCallback(async () => {
    if (!slug) return
    setLoading(true)
    setError('')
    try {
      const postRes = await getBlogPostBySlug(slug)
      setPost(postRes.data)
      if (currentUserId) {
        const favRes = await getBlogPostFavoriteStatus(postRes.data.id)
        setIsFavorited(favRes.data.is_favorited)
      } else {
        setIsFavorited(false)
      }
    } catch {
      setError('文章加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [slug, currentUserId])

  useEffect(() => {
    fetchPost()
    window.scrollTo(0, 0)
  }, [fetchPost])

  useEffect(() => {
    getBlogCategories().then((res) => setCategories(res.data)).catch(() => {})
  }, [])

  const handleLogout = useLogout()

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
        <AppTopNav onLogout={handleLogout} />
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-muted)' }}>
          加载中...
        </div>
        <Footer />
      </div>
    )
  }

  if (error || !post) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
        <AppTopNav onLogout={handleLogout} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--color-muted)', gap: 'var(--spacing-md)' }}>
          <BookOpen size={48} style={{ opacity: 0.3 }} />
          <p style={{ fontSize: 16, margin: 0 }}>{error || '文章不存在'}</p>
          <button
            onClick={() => navigate('/blogs')}
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
            返回博客列表
          </button>
        </div>
        <Footer />
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      <AppTopNav onLogout={handleLogout} />

      {/* Article Header */}
      <section
        style={{
          backgroundColor: 'var(--color-surface-soft)',
          padding: 'var(--spacing-section) var(--spacing-xl) var(--spacing-xl)',
        }}
      >
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {/* Back */}
          <button
            onClick={() => navigate('/blogs')}
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
            返回博客列表
          </button>

          {/* Category & Tags */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-xs)', marginBottom: 'var(--spacing-md)', flexWrap: 'wrap' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: '4px 12px',
                borderRadius: 'var(--rounded-pill)',
                backgroundColor: 'var(--color-canvas)',
                fontSize: 12,
                fontWeight: 500,
                color: 'var(--color-primary)',
              }}
            >
              <BookOpen size={12} />
              {post.category.name}
            </span>
            {post.tags.map((tag) => (
              <span
                key={tag}
                style={{
                  padding: '4px 12px',
                  borderRadius: 'var(--rounded-pill)',
                  backgroundColor: 'var(--color-canvas)',
                  fontSize: 12,
                  fontWeight: 500,
                  color: 'var(--color-muted)',
                }}
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Title */}
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(28px, 4vw, 48px)',
              fontWeight: 400,
              lineHeight: 1.1,
              letterSpacing: '-1px',
              color: 'var(--color-ink)',
              margin: '0 0 var(--spacing-md)',
            }}
          >
            {post.title}
          </h1>

          {/* Admin Actions */}
          {isSuperAdmin && (
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)', marginBottom: 'var(--spacing-md)', flexWrap: 'wrap' }}>
              <button
                onClick={() => setShowEditor(true)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-canvas)',
                  border: '1px solid var(--color-hairline)',
                  fontSize: 13,
                  color: 'var(--color-muted)',
                  cursor: 'pointer',
                }}
              >
                <Edit3 size={12} />
                编辑
              </button>
              <button
                onClick={async () => {
                  if (!post) return
                  try {
                    if (post.status === 'published') {
                      await unpublishBlogPost(post.id)
                      toast.success('文章已下线')
                    } else {
                      await publishBlogPost(post.id)
                      toast.success('文章已发布')
                    }
                    fetchPost()
                  } catch {
                    toast.error('操作失败')
                  }
                }}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-canvas)',
                  border: '1px solid var(--color-hairline)',
                  fontSize: 13,
                  color: 'var(--color-muted)',
                  cursor: 'pointer',
                }}
              >
                {post.status === 'published' ? <Minus size={12} /> : <Plus size={12} />}
                {post.status === 'published' ? '下线' : '发布'}
              </button>
              <button
                onClick={async () => {
                  if (!post) return
                  if (!window.confirm('确定要删除这篇文章吗？此操作不可撤销。')) return
                  try {
                    await deleteBlogPost(post.id)
                    toast.success('文章已删除')
                    navigate('/blogs')
                  } catch {
                    toast.error('删除失败')
                  }
                }}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-canvas)',
                  border: '1px solid var(--color-hairline)',
                  fontSize: 13,
                  color: 'var(--color-error)',
                  cursor: 'pointer',
                }}
              >
                <Trash2 size={12} />
                删除
              </button>
            </div>
          )}

          {/* Meta: Author + Date + Views + Comments */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)', fontSize: 14, color: 'var(--color-muted-soft)', flexWrap: 'wrap' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: 'var(--rounded-full)',
                  backgroundColor: 'var(--color-surface-card)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-primary)',
                  overflow: 'hidden',
                }}
              >
                {post.author.avatar_url ? (
                  <img src={post.author.avatar_url} alt={post.author.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <User size={12} />
                )}
              </div>
              <span style={{ fontWeight: 500, color: 'var(--color-body-strong)' }}>
                {post.author.username}
              </span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Clock size={14} />
              {formatDate(post.created_at)}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Eye size={14} />
              {post.view_count} 阅读
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <MessageCircle size={14} />
              {post.comment_count} 评论
            </span>
            <button
              onClick={async () => {
                if (favoriting) return
                setFavoriting(true)
                try {
                  if (isFavorited) {
                    await unfavoriteBlogPost(post.id)
                    setIsFavorited(false)
                  } else {
                    await favoriteBlogPost(post.id)
                    setIsFavorited(true)
                  }
                } catch {
                  toast.error(isFavorited ? '取消收藏失败' : '收藏失败')
                } finally {
                  setFavoriting(false)
                }
              }}
              disabled={favoriting}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 14,
                fontWeight: 500,
                color: isFavorited ? 'var(--color-primary)' : 'var(--color-muted-soft)',
                background: 'transparent',
                border: 'none',
                cursor: favoriting ? 'not-allowed' : 'pointer',
                padding: 0,
              }}
            >
              <Heart size={14} fill={isFavorited ? 'var(--color-primary)' : 'none'} />
              {isFavorited ? '已收藏' : '收藏'}
            </button>
          </div>

          {/* Cover Image */}
          {post.cover_image_url && (
            <div
              style={{
                marginTop: 'var(--spacing-xl)',
                borderRadius: 'var(--rounded-lg)',
                overflow: 'hidden',
              }}
            >
              <img
                src={post.cover_image_url}
                alt={post.title}
                style={{ width: '100%', maxHeight: 420, objectFit: 'cover', display: 'block' }}
              />
            </div>
          )}
        </div>
      </section>

      {/* Article Body */}
      <section style={{ padding: 'var(--spacing-xl) var(--spacing-xl)', flex: 1 }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <MarkdownContent content={post.content_md} />
          <PostNavigation prev={post.prev_post} next={post.next_post} />
          <CommentSection postId={post.id} totalCommentCount={post.comment_count} />
        </div>
      </section>

      <Footer />

      {showEditor && post && (
        <BlogEditorModal
          post={post}
          categories={categories}
          onClose={() => setShowEditor(false)}
          onSubmit={async (data) => {
            setSubmitting(true)
            try {
              const res = await updateBlogPost(post.id, data, data.file)
              toast.success('文章更新成功')
              setShowEditor(false)
              const newSlug = res.data.slug
              if (newSlug && newSlug !== slug) {
                navigate(`/blogs/${newSlug}`, { replace: true })
              } else {
                fetchPost()
              }
            } catch {
              toast.error('文章更新失败')
            } finally {
              setSubmitting(false)
            }
          }}
          submitting={submitting}
        />
      )}
    </div>
  )
}
