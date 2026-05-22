import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  User,
  Eye,
  MessageCircle,
  Clock,
  ArrowLeft,
  Send,
  Heart,
  Trash2,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  Edit3,
  X,
} from 'lucide-react'
import {
  getForumPostById,
  deleteForumPost,
  updateForumPost,
  getForumReplies,
  createForumReply,
  deleteForumReply,
  getForumZoneById,
} from '../api/forum'
import { getCommentList, createComment, deleteComment, likeComment, unlikeComment } from '../api/comments'
import { favoriteForumPost, unfavoriteForumPost, getFavoriteForumPosts } from '../api/favorites'
import { getUser } from '../utils/auth'
import AppTopNav from '../components/AppTopNav'
import Footer from '../components/Footer'
import { useLogout } from '../hooks/useLogout'
import { formatDate, formatDateTime } from '../utils/format'
import type { ForumPost, ForumReply, ForumZone } from '../types/forum'
import type { CommentResponse } from '../types/comments'

const REPLY_PAGE_SIZE = 10
const COMMENT_PAGE_SIZE = 5

/* ─── Edit Post Modal ─── */
function EditPostModal({
  post,
  onClose,
  onSuccess,
}: {
  post: ForumPost
  onClose: () => void
  onSuccess: () => void
}) {
  const [title, setTitle] = useState(post.title)
  const [content, setContent] = useState(post.content)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) return
    setSubmitting(true)
    try {
      await updateForumPost(post.id, {
        title: title.trim(),
        content: content.trim(),
      })
      onSuccess()
      onClose()
    } catch {
      alert('编辑失败，请稍后重试')
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
            编辑帖子
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
              <Edit3 size={14} />
              {submitting ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Text Input for Reply ─── */
function TextInput({
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

/* ─── Comment Item (nested reply inside forum reply) ─── */
function CommentItem({
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
  onReply: (nestedParentId: number, username: string) => void
}) {
  const canDelete = currentUserId === comment.user_id || isAdmin

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
              onClick={() => onReply(comment.id, comment.user.username)}
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
        </div>
      </div>
    </div>
  )
}

/* ─── Comment Section for a Forum Reply ─── */
function ReplyCommentSection({
  replyId,
}: {
  replyId: number
}) {
  const currentUser = getUser()
  const [comments, setComments] = useState<CommentResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [newComment, setNewComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [replyingTo, setReplyingTo] = useState<{ id: number; username: string } | null>(null)
  const [showCommentInput, setShowCommentInput] = useState(false)

  const totalPages = Math.ceil(total / COMMENT_PAGE_SIZE)

  const fetchComments = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getCommentList({
        target_type: 'forum_reply',
        target_id: replyId,
        sort_by: 'time_asc',
        skip: (page - 1) * COMMENT_PAGE_SIZE,
        limit: COMMENT_PAGE_SIZE,
      })
      setComments(res.data.items)
      setTotal(res.data.total)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [replyId, page])

  useEffect(() => {
    fetchComments()
  }, [fetchComments])

  const handleSubmit = async () => {
    if (!newComment.trim()) return
    setSubmitting(true)
    try {
      await createComment({
        target_type: 'forum_reply',
        target_id: replyId,
        content: newComment.trim(),
      })
      setNewComment('')
      setPage(1)
      fetchComments()
    } catch {
      alert('评论发表失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleNestedReply = async (rawContent: string) => {
    if (!replyingTo) return
    setSubmitting(true)
    try {
      const content = `@${replyingTo.username}：${rawContent}`
      await createComment({
        target_type: 'forum_reply',
        target_id: replyId,
        parent_id: replyId,
        is_nested: true,
        nested_parent_id: replyingTo.id,
        content,
      })
      setReplyingTo(null)
      fetchComments()
    } catch {
      alert('回复失败')
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
      alert('删除失败')
    }
  }

  return (
    <div
      style={{
        marginTop: 'var(--spacing-md)',
        paddingLeft: 'var(--spacing-md)',
        borderLeft: '2px solid var(--color-hairline-soft)',
      }}
    >
      {/* Input toggle */}
      {!showCommentInput ? (
        <div style={{ marginBottom: 'var(--spacing-md)' }}>
          <button
            onClick={() => setShowCommentInput(true)}
            disabled={!currentUser}
            style={{
              padding: '8px 16px',
              backgroundColor: 'transparent',
              color: !currentUser ? 'var(--color-muted)' : 'var(--color-primary)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 13,
              fontWeight: 500,
              border: '1px solid var(--color-hairline)',
              cursor: !currentUser ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <MessageCircle size={12} />
            {currentUser ? '写评论' : '请先登录后评论'}
          </button>
        </div>
      ) : (
        <div
          style={{
            backgroundColor: 'var(--color-canvas)',
            borderRadius: 'var(--rounded-md)',
            padding: 'var(--spacing-md)',
            marginBottom: 'var(--spacing-md)',
          }}
        >
          <textarea
            placeholder='写下你的评论...'
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            disabled={submitting}
            style={{
              width: '100%',
              minHeight: 60,
              padding: 'var(--spacing-sm)',
              borderRadius: 'var(--rounded-md)',
              border: '1px solid var(--color-hairline)',
              backgroundColor: 'var(--color-surface-soft)',
              fontSize: 14,
              lineHeight: 1.6,
              color: 'var(--color-ink)',
              resize: 'vertical',
              outline: 'none',
              fontFamily: 'var(--font-body)',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)' }}>
            <button
              onClick={() => {
                setShowCommentInput(false)
                setNewComment('')
              }}
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
            <button
              onClick={handleSubmit}
              disabled={submitting || !newComment.trim()}
              style={{
                padding: '8px 16px',
                backgroundColor: !newComment.trim() ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
                color: !newComment.trim() ? 'var(--color-muted)' : 'var(--color-on-primary)',
                borderRadius: 'var(--rounded-md)',
                fontSize: 13,
                fontWeight: 500,
                border: 'none',
                cursor: !newComment.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <Send size={12} />
              {submitting ? '发表中...' : '发表评论'}
            </button>
          </div>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div style={{ padding: 'var(--spacing-sm) 0', fontSize: 13, color: 'var(--color-muted)' }}>加载评论中...</div>
      ) : comments.length === 0 ? (
        <div style={{ padding: 'var(--spacing-sm) 0', fontSize: 13, color: 'var(--color-muted)' }}>暂无评论</div>
      ) : (
        <>
          {comments.map((comment) => (
            <div key={comment.id}>
              <CommentItem
                comment={comment}
                currentUserId={currentUser?.id ?? null}
                isAdmin={currentUser?.permission === 2}
                onLike={handleLike}
                onUnlike={handleUnlike}
                onDelete={handleDelete}
                onReply={(id, username) => {
                  setReplyingTo({ id, username })
                }}
              />
              {replyingTo?.id === comment.id && (
                <div style={{ paddingLeft: 'var(--spacing-xl)' }}>
                  <TextInput
                    placeholder={`回复 @${replyingTo.username}：`}
                    onSubmit={handleNestedReply}
                    onCancel={() => setReplyingTo(null)}
                    submitText="回复"
                  />
                </div>
              )}
            </div>
          ))}

          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-xs)', padding: 'var(--spacing-sm) 0' }}>
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--rounded-md)',
                  border: '1px solid var(--color-hairline)',
                  backgroundColor: 'var(--color-canvas)',
                  cursor: page === 1 ? 'not-allowed' : 'pointer',
                  opacity: page === 1 ? 0.5 : 1,
                  color: 'var(--color-ink)',
                  fontSize: 12,
                }}
              >
                <ChevronLeft size={12} />
              </button>
              <span style={{ display: 'flex', alignItems: 'center', padding: '0 var(--spacing-sm)', fontSize: 13, color: 'var(--color-muted)' }}>
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--rounded-md)',
                  border: '1px solid var(--color-hairline)',
                  backgroundColor: 'var(--color-canvas)',
                  cursor: page === totalPages ? 'not-allowed' : 'pointer',
                  opacity: page === totalPages ? 0.5 : 1,
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
  )
}

/* ─── Forum Reply Item ─── */
function ForumReplyItem({
  reply,
  index,
  postId,
  currentUserId,
  isAdmin,
  isZoneManager,
  onDelete,
  onRefreshReplies,
}: {
  reply: ForumReply
  index: number
  postId: number
  currentUserId: number | null
  isAdmin: boolean
  isZoneManager: boolean
  onDelete: (id: number) => void
  onRefreshReplies?: () => void
}) {
  const canDelete = currentUserId === reply.user_id || isAdmin || isZoneManager
  const [showComments, setShowComments] = useState(false)
  const [showReplyInput, setShowReplyInput] = useState(false)

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-soft)',
        borderRadius: 'var(--rounded-lg)',
        border: '1px solid var(--color-hairline-soft)',
        padding: 'var(--spacing-lg)',
        position: 'relative',
      }}
    >
      {/* Floor badge */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          right: 16,
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--color-primary)',
          backgroundColor: 'rgba(204, 120, 92, 0.08)',
          padding: '2px 10px',
          borderRadius: 'var(--rounded-pill)',
        }}
      >
        #{index}楼
      </div>

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
          {reply.user.avatar_url ? (
            <img src={reply.user.avatar_url} alt={reply.user.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <User size={18} />
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 4, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-body-strong)' }}>
              {reply.user.username}
            </span>
            <span style={{ fontSize: 12, color: 'var(--color-muted-soft)' }}>
              {formatDateTime(reply.created_at)}
            </span>
          </div>

          <p style={{ fontSize: 15, lineHeight: 1.7, color: 'var(--color-body)', margin: '0 0 var(--spacing-sm)' }}>
            {reply.content}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
            <span
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--color-muted-soft)',
              }}
            >
              <Heart size={14} />
              {reply.likecount}
            </span>

            <button
              onClick={() => setShowReplyInput((s) => !s)}
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: showReplyInput ? 'var(--color-primary)' : 'var(--color-muted-soft)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              {showReplyInput ? '取消回复' : '回复'}
            </button>

            <button
              onClick={() => setShowComments((s) => !s)}
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
              {showComments ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {reply.comment_count > 0 ? `${reply.comment_count} 条回复` : '查看回复'}
            </button>

            {canDelete && (
              <button
                onClick={() => {
                  if (window.confirm('确定要删除这条回复吗？')) {
                    onDelete(reply.id)
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
                  display: 'flex',
                  alignItems: 'center',
                  gap: 3,
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

          {showReplyInput && (
            <div style={{ marginTop: 'var(--spacing-sm)' }}>
              <TextInput
                placeholder="写下你的回复..."
                onSubmit={async (content) => {
                  try {
                    await createForumReply(postId, { content })
                    setShowReplyInput(false)
                    onRefreshReplies?.()
                  } catch {
                    alert('回复发表失败')
                  }
                }}
                onCancel={() => setShowReplyInput(false)}
                submitText="发表回复"
              />
            </div>
          )}

          {showComments && (
            <ReplyCommentSection replyId={reply.id} />
          )}
        </div>
      </div>
    </div>
  )
}

/* ─── Main Page ─── */
export default function ForumPostDetailPage() {
  const { postId } = useParams<{ postId: string }>()
  const navigate = useNavigate()
  const currentUser = getUser()
  const [post, setPost] = useState<ForumPost | null>(null)
  const [zone, setZone] = useState<ForumZone | null>(null)
  const [replies, setReplies] = useState<ForumReply[]>([])
  const [totalReplies, setTotalReplies] = useState(0)
  const [replyPage, setReplyPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showEditModal, setShowEditModal] = useState(false)
  const [showMainReplyInput, setShowMainReplyInput] = useState(false)
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriting, setFavoriting] = useState(false)

  const totalReplyPages = Math.ceil(totalReplies / REPLY_PAGE_SIZE)

  const fetchPost = useCallback(async () => {
    if (!postId) return
    const id = parseInt(postId, 10)
    if (isNaN(id)) {
      setError('无效的帖子 ID')
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    try {
      const [postRes, favRes] = await Promise.all([
        getForumPostById(id),
        getFavoriteForumPosts({ limit: 100 }),
      ])
      setPost(postRes.data)
      setIsFavorited(favRes.data.items.some((item) => item.id === postRes.data.id))
      // 获取分区信息以判断区主权限
      try {
        const zoneRes = await getForumZoneById(postRes.data.zone_id)
        setZone(zoneRes.data)
      } catch {
        // ignore zone fetch error
      }
    } catch {
      setError('帖子加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [postId])

  const fetchReplies = useCallback(async () => {
    if (!postId) return
    const id = parseInt(postId, 10)
    if (isNaN(id)) return
    try {
      const res = await getForumReplies(id, {
        skip: (replyPage - 1) * REPLY_PAGE_SIZE,
        limit: REPLY_PAGE_SIZE,
      })
      setReplies(res.data.items)
      setTotalReplies(res.data.total)
    } catch {
      // ignore
    }
  }, [postId, replyPage])

  useEffect(() => {
    fetchPost()
    window.scrollTo(0, 0)
  }, [fetchPost])

  useEffect(() => {
    fetchReplies()
  }, [fetchReplies])

  const handleLogout = useLogout()

  const handleDeletePost = async () => {
    if (!post) return
    if (!window.confirm('确定要删除这篇帖子吗？此操作不可撤销。')) return
    try {
      await deleteForumPost(post.id)
      navigate(`/forums/z/${post.zone_id}`)
    } catch {
      alert('删除失败')
    }
  }

  const handleDeleteReply = async (replyId: number) => {
    try {
      await deleteForumReply(replyId)
      fetchReplies()
    } catch {
      alert('删除失败')
    }
  }

  const isPostAuthor = currentUser?.id === post?.user_id
  const isAdmin = currentUser?.permission === 2
  const isZoneManager = currentUser?.id === zone?.manager_id

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
          <MessageCircle size={48} style={{ opacity: 0.3 }} />
          <p style={{ fontSize: 16, margin: 0 }}>{error || '帖子不存在'}</p>
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
            返回论坛
          </button>
        </div>
        <Footer />
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      <AppTopNav onLogout={handleLogout} />

      {/* Post Header */}
      <section
        style={{
          backgroundColor: 'var(--color-surface-soft)',
          padding: 'var(--spacing-section) var(--spacing-xl) var(--spacing-xl)',
        }}
      >
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
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
            返回论坛
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
            <MessageCircle size={12} />
            论坛帖子
          </div>

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
                {post.user.avatar_url ? (
                  <img src={post.user.avatar_url} alt={post.user.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <User size={12} />
                )}
              </div>
              <span style={{ fontWeight: 500, color: 'var(--color-body-strong)' }}>
                {post.user.username}
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
              {post.reply_count} 回复
            </span>
            <button
              onClick={async () => {
                if (favoriting) return
                setFavoriting(true)
                try {
                  if (isFavorited) {
                    await unfavoriteForumPost(post.id)
                    setIsFavorited(false)
                  } else {
                    await favoriteForumPost(post.id)
                    setIsFavorited(true)
                  }
                } catch {
                  alert(isFavorited ? '取消收藏失败' : '收藏失败')
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

          {(isPostAuthor || isAdmin || isZoneManager) && (
            <div style={{ display: 'flex', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-md)' }}>
              <button
                onClick={() => setShowEditModal(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  fontSize: 13,
                  fontWeight: 500,
                  color: 'var(--color-muted)',
                  backgroundColor: 'var(--color-canvas)',
                  border: '1px solid var(--color-hairline)',
                  borderRadius: 'var(--rounded-md)',
                  cursor: 'pointer',
                }}
              >
                <Edit3 size={13} />
                编辑
              </button>
              <button
                onClick={handleDeletePost}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '6px 12px',
                  fontSize: 13,
                  fontWeight: 500,
                  color: 'var(--color-error)',
                  backgroundColor: 'var(--color-canvas)',
                  border: '1px solid var(--color-hairline)',
                  borderRadius: 'var(--rounded-md)',
                  cursor: 'pointer',
                }}
              >
                <Trash2 size={13} />
                删除
              </button>
            </div>
          )}
        </div>
      </section>

      {/* Post Content */}
      <section style={{ padding: 'var(--spacing-xl) var(--spacing-xl)', flex: 1 }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <div
            style={{
              fontSize: 16,
              lineHeight: 1.75,
              color: 'var(--color-body)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {post.content}
          </div>

          {/* Reply Section */}
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
                回复
                <span style={{ fontSize: 16, color: 'var(--color-muted-soft)', fontFamily: 'var(--font-body)' }}>
                  ({post.reply_count})
                </span>
              </h2>
            </div>

            {/* Reply Input */}
            {!showMainReplyInput ? (
              <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                <button
                  onClick={() => setShowMainReplyInput(true)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 20px',
                    backgroundColor: 'var(--color-primary)',
                    color: 'var(--color-on-primary)',
                    borderRadius: 'var(--rounded-md)',
                    fontSize: 14,
                    fontWeight: 500,
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'background-color 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-primary)'
                  }}
                >
                  <MessageCircle size={14} />
                  发表回复
                </button>
              </div>
            ) : (
              <div
                style={{
                  backgroundColor: 'var(--color-surface-card)',
                  borderRadius: 'var(--rounded-lg)',
                  padding: 'var(--spacing-lg)',
                  marginBottom: 'var(--spacing-lg)',
                }}
              >
                <TextInput
                  placeholder="发表你的回复..."
                  onSubmit={async (content) => {
                    try {
                      await createForumReply(post.id, { content })
                      setShowMainReplyInput(false)
                      fetchReplies()
                    } catch {
                      alert('回复发表失败')
                    }
                  }}
                  onCancel={() => setShowMainReplyInput(false)}
                  submitText="发表回复"
                />
              </div>
            )}

            {/* Reply List */}
            {replies.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 'var(--spacing-xl) 0', color: 'var(--color-muted)' }}>
                <MessageCircle size={36} style={{ marginBottom: 'var(--spacing-sm)', opacity: 0.3 }} />
                <p style={{ fontSize: 14, margin: 0 }}>暂无回复，快来抢沙发吧</p>
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--spacing-md)',
                }}
              >
                {replies.map((reply, idx) => (
                  <ForumReplyItem
                    key={reply.id}
                    reply={reply}
                    index={(replyPage - 1) * REPLY_PAGE_SIZE + idx + 1}
                    postId={post.id}
                    currentUserId={currentUser?.id ?? null}
                    isAdmin={isAdmin}
                    isZoneManager={isZoneManager}
                    onDelete={handleDeleteReply}
                    onRefreshReplies={fetchReplies}
                  />
                ))}
              </div>
            )}

            {/* Reply Pagination */}
            {totalReplyPages > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-xs)', marginTop: 'var(--spacing-lg)' }}>
                <button
                  onClick={() => setReplyPage((p) => Math.max(1, p - 1))}
                  disabled={replyPage === 1}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--rounded-md)',
                    border: '1px solid var(--color-hairline)',
                    backgroundColor: 'var(--color-canvas)',
                    cursor: replyPage === 1 ? 'not-allowed' : 'pointer',
                    opacity: replyPage === 1 ? 0.5 : 1,
                    color: 'var(--color-ink)',
                    fontSize: 13,
                  }}
                >
                  <ChevronLeft size={14} />
                </button>
                <span style={{ display: 'flex', alignItems: 'center', padding: '0 var(--spacing-sm)', fontSize: 14, color: 'var(--color-muted)' }}>
                  {replyPage} / {totalReplyPages}
                </span>
                <button
                  onClick={() => setReplyPage((p) => Math.min(totalReplyPages, p + 1))}
                  disabled={replyPage === totalReplyPages}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--rounded-md)',
                    border: '1px solid var(--color-hairline)',
                    backgroundColor: 'var(--color-canvas)',
                    cursor: replyPage === totalReplyPages ? 'not-allowed' : 'pointer',
                    opacity: replyPage === totalReplyPages ? 0.5 : 1,
                    color: 'var(--color-ink)',
                    fontSize: 13,
                  }}
                >
                  <ChevronLeft size={14} style={{ transform: 'rotate(180deg)' }} />
                </button>
              </div>
            )}
          </section>
        </div>
      </section>

      <Footer />

      {showEditModal && (
        <EditPostModal
          post={post}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => {
            fetchPost()
          }}
        />
      )}
    </div>
  )
}
