import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Bookmark, Heart, MessageCircle, Send, Trash2, Eye } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Avatar from '@/components/ui/Avatar'
import Textarea from '@/components/ui/Textarea'
import { formatDateTime } from '@/lib/utils'
import { cn } from '@/lib/utils'

const MOCK_POST = {
  id: 1,
  title: 'React 19 的 use() Hook 有什么实际使用场景？',
  content: '看了文档 but 还是不太理解在什么情况下应该用 use() 而不是 useEffect。\n\n有人能结合实际项目经验讲解一下吗？特别是在数据获取和条件渲染的场景下。',
  zone_id: 1,
  user: { username: 'CuriousDev', avatar_url: null },
  view_count: 234,
  reply_count: 3,
  created_at: '2024-01-15T10:00:00',
}

const MOCK_REPLIES = [
  {
    id: 1,
    content: 'use() 最大的好处是可以在条件语句中使用，而 useEffect 不行。比如在 Suspense 边界内，你可以根据条件决定是否 use(promise)。',
    user: { username: 'ReactExpert', avatar_url: null },
    likecount: 15,
    comment_count: 2,
    created_at: '2024-01-15T10:30:00',
  },
  {
    id: 2,
    content: '我补充一点，use() 还可以用于 Context，让你可以在 render 过程中读取 Context 值而不用 useContext。',
    user: { username: 'ContextLover', avatar_url: null },
    likecount: 8,
    comment_count: 0,
    created_at: '2024-01-15T11:00:00',
  },
  {
    id: 3,
    content: '实际项目中，我主要用它来处理路由级别的数据预加载，配合 Suspense 做骨架屏体验非常好。',
    user: { username: 'RouteMaster', avatar_url: null },
    likecount: 12,
    comment_count: 1,
    created_at: '2024-01-15T12:00:00',
  },
]

export default function PostDetailPage() {
  useParams()
  const [isFavorited, setIsFavorited] = useState(false)
  const [replyText, setReplyText] = useState('')

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Back */}
      <Link to="/forum/frontend" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="h-4 w-4" />
        返回分区
      </Link>

      {/* Post */}
      <Card>
        <CardContent className="p-6">
          {/* Post Header */}
          <div className="flex items-start gap-4">
            <Avatar name={MOCK_POST.user.username} size="lg" />
            <div className="flex-1">
              <h1 className="text-xl font-bold">{MOCK_POST.title}</h1>
              <div className="mt-2 flex items-center gap-3 text-sm text-muted-foreground">
                <span className="font-medium text-foreground">{MOCK_POST.user.username}</span>
                <span>{formatDateTime(MOCK_POST.created_at)}</span>
                <span className="flex items-center gap-1">
                  <Eye className="h-3.5 w-3.5" />
                  {MOCK_POST.view_count}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsFavorited(!isFavorited)}
              >
                <Bookmark className={cn('h-4 w-4', isFavorited && 'fill-primary text-primary')} />
              </Button>
              <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Post Content */}
          <div className="mt-6 text-foreground leading-relaxed whitespace-pre-line">
            {MOCK_POST.content}
          </div>
        </CardContent>
      </Card>

      {/* Replies */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">回复 ({MOCK_REPLIES.length})</h3>

        {/* Reply Input */}
        <div className="flex gap-3 mb-6">
          <Avatar name="当前用户" size="md" />
          <div className="flex-1">
            <Textarea
              placeholder="发表你的回复..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              className="min-h-[80px]"
            />
            <div className="mt-2 flex justify-end">
              <Button size="sm" className="gap-1">
                <Send className="h-3.5 w-3.5" />
                回复
              </Button>
            </div>
          </div>
        </div>

        {/* Replies List */}
        <div className="space-y-4">
          {MOCK_REPLIES.map(reply => (
            <Card key={reply.id} className="animate-fade-in">
              <CardContent className="p-4">
                <div className="flex gap-3">
                  <Avatar name={reply.user.username} size="md" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{reply.user.username}</span>
                      <span className="text-xs text-muted-foreground">{formatDateTime(reply.created_at)}</span>
                    </div>
                    <p className="mt-2 text-sm text-foreground leading-relaxed">{reply.content}</p>
                    <div className="mt-3 flex items-center gap-4">
                      <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                        <Heart className="h-3.5 w-3.5" />
                        <span>{reply.likecount}</span>
                      </button>
                      <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                        <MessageCircle className="h-3.5 w-3.5" />
                        <span>{reply.comment_count} 评论</span>
                      </button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
