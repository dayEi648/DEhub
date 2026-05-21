import { useState } from 'react'
import { Heart, MessageCircle, Send, ChevronDown, ChevronUp, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Comment } from '@/types'
import Avatar from './Avatar'
import Button from './Button'
import Textarea from './Textarea'
import { formatDateTime } from '@/lib/utils'

// Mock data for demo
const MOCK_COMMENTS: Comment[] = [
  {
    id: 1,
    target_type: 'blog_post',
    target_id: 1,
    parent_id: null,
    user_id: 2,
    content: '这篇文章写得太好了！帮我解决了很多困惑，感谢分享。',
    is_nested: false,
    nested_parent_id: null,
    likecount: 12,
    is_liked: false,
    created_at: '2024-01-15T10:30:00',
    user: { id: 2, username: 'CodeMaster', avatar_url: null },
  },
  {
    id: 2,
    target_type: 'blog_post',
    target_id: 1,
    parent_id: 1,
    user_id: 3,
    content: '确实，特别是关于性能优化那部分，非常实用。',
    is_nested: false,
    nested_parent_id: null,
    likecount: 5,
    is_liked: true,
    created_at: '2024-01-15T11:00:00',
    user: { id: 3, username: 'DevNewbie', avatar_url: null },
  },
  {
    id: 3,
    target_type: 'blog_post',
    target_id: 1,
    parent_id: 1,
    user_id: 4,
    content: '同意！我也在实践中验证了这些方法。',
    is_nested: true,
    nested_parent_id: 2,
    likecount: 2,
    is_liked: false,
    created_at: '2024-01-15T11:30:00',
    user: { id: 4, username: 'FullStackPro', avatar_url: null },
  },
  {
    id: 4,
    target_type: 'blog_post',
    target_id: 1,
    parent_id: null,
    user_id: 5,
    content: '期待下一篇关于部署的教程！',
    is_nested: false,
    nested_parent_id: null,
    likecount: 8,
    is_liked: false,
    created_at: '2024-01-16T09:00:00',
    user: { id: 5, username: 'OpsGuy', avatar_url: null },
  },
]

interface CommentItemProps {
  comment: Comment
  replies: Comment[]
  onReply: (parentId: number) => void
}

function CommentItem({ comment, replies, onReply }: CommentItemProps) {
  const [showReplies, setShowReplies] = useState(false)
  const [liked, setLiked] = useState(comment.is_liked)
  const [likeCount, setLikeCount] = useState(comment.likecount)

  const handleLike = () => {
    setLiked(!liked)
    setLikeCount(prev => liked ? prev - 1 : prev + 1)
  }

  return (
    <div className="animate-fade-in">
      <div className="flex gap-3">
        <Avatar name={comment.user.username} size="md" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">{comment.user.username}</span>
            <span className="text-xs text-muted-foreground">{formatDateTime(comment.created_at)}</span>
          </div>
          <p className="mt-1 text-sm text-foreground leading-relaxed">{comment.content}</p>
          <div className="mt-2 flex items-center gap-4">
            <button
              onClick={handleLike}
              className={cn(
                'flex items-center gap-1 text-xs transition-colors',
                liked ? 'text-red-500' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <Heart className={cn('h-3.5 w-3.5', liked && 'fill-current')} />
              <span>{likeCount}</span>
            </button>
            <button
              onClick={() => onReply(comment.id)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <MessageCircle className="h-3.5 w-3.5" />
              <span>回复</span>
            </button>
            {/* Mock delete for author/admin */}
            <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive transition-colors ml-auto">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Replies */}
          {replies.length > 0 && (
            <div className="mt-2">
              <button
                onClick={() => setShowReplies(!showReplies)}
                className="flex items-center gap-1 text-xs text-primary hover:underline"
              >
                {showReplies ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                <span>{replies.length} 条回复</span>
              </button>
              {showReplies && (
                <div className="mt-3 space-y-3 pl-4 border-l-2 border-border">
                  {replies.map(reply => (
                    <div key={reply.id} className="animate-fade-in">
                      <div className="flex items-center gap-2">
                        <Avatar name={reply.user.username} size="sm" />
                        <span className="text-sm font-semibold">{reply.user.username}</span>
                        {reply.is_nested && (
                          <span className="text-xs text-muted-foreground">
                            回复 @{(MOCK_COMMENTS.find(c => c.id === reply.nested_parent_id)?.user.username) || '某人'}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">{formatDateTime(reply.created_at)}</span>
                      </div>
                      <p className="mt-1 text-sm text-foreground">{reply.content}</p>
                      <div className="mt-1 flex items-center gap-3">
                        <button
                          onClick={() => {}}
                          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Heart className="h-3 w-3" />
                          <span>{reply.likecount}</span>
                        </button>
                        <button
                          onClick={() => onReply(reply.id)}
                          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                          回复
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface CommentSectionProps {
  targetType: string
  targetId: number
}

export default function CommentSection(_props: CommentSectionProps) {
  const [commentText, setCommentText] = useState('')
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyText, setReplyText] = useState('')

  // Separate top-level comments and replies
  const topComments = MOCK_COMMENTS.filter(c => c.parent_id === null)
  const getReplies = (parentId: number) => MOCK_COMMENTS.filter(c => c.parent_id === parentId)

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">评论 ({MOCK_COMMENTS.length})</h3>

      {/* New Comment */}
      <div className="flex gap-3">
        <Avatar name="当前用户" size="md" />
        <div className="flex-1">
          <Textarea
            placeholder="写下你的评论..."
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            className="min-h-[80px]"
          />
          <div className="mt-2 flex justify-end">
            <Button size="sm" className="gap-1">
              <Send className="h-3.5 w-3.5" />
              发表评论
            </Button>
          </div>
        </div>
      </div>

      {/* Comments List */}
      <div className="space-y-6">
        {topComments.map(comment => (
          <div key={comment.id}>
            <CommentItem
              comment={comment}
              replies={getReplies(comment.id)}
              onReply={(id) => {
                setReplyingTo(replyingTo === id ? null : id)
                setReplyText('')
              }}
            />
            {/* Inline Reply Input */}
            {replyingTo === comment.id && (
              <div className="mt-3 ml-12 flex gap-3 animate-fade-in">
                <Avatar name="当前用户" size="sm" />
                <div className="flex-1">
                  <Textarea
                    placeholder={`回复 @${comment.user.username}...`}
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    className="min-h-[60px]"
                  />
                  <div className="mt-2 flex justify-end gap-2">
                    <Button variant="ghost" size="sm" onClick={() => setReplyingTo(null)}>
                      取消
                    </Button>
                    <Button size="sm">发送回复</Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
