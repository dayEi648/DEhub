import { useParams, Link } from 'react-router-dom'
import { useState } from 'react'
import { Bookmark, ArrowLeft, ArrowRight, Clock, Eye, MessageCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import Avatar from '@/components/ui/Avatar'
import CommentSection from '@/components/ui/CommentSection'
import { formatDateTime } from '@/lib/utils'

const MOCK_POST = {
  id: 1,
  title: 'React 19 新特性详解：从 use 到 Server Components',
  slug: 'react-19-features',
  summary: 'React 19 带来了许多激动人心的新特性...',
  content_md: '# React 19 新特性详解\n\nReact 19 是 React 团队发布的最新 major 版本，带来了许多重要的新特性和改进。\n\n## use() Hook\n\n`use()` 是一个新的 Hook，可以在条件语句中使用...\n\n## Server Components\n\nServer Components 允许在服务器端渲染组件...\n\n## Actions\n\nActions 提供了一种处理表单提交的新方式...',
  cover_image_url: null,
  category: { name: '前端开发' },
  tags: ['React', 'Frontend', 'JavaScript'],
  status: 'published',
  view_count: 1205,
  comment_count: 32,
  created_at: '2024-01-15T10:00:00',
  updated_at: '2024-01-15T12:00:00',
  prev_post: { id: 0, title: 'FastAPI 性能优化指南', slug: 'fastapi-performance' },
  next_post: { id: 2, title: 'LangGraph 工作流设计模式', slug: 'langgraph-patterns' },
}

export default function BlogDetailPage() {
  useParams()
  const [isFavorited, setIsFavorited] = useState(false)

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Back Link */}
      <Link to="/blog" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6">
        <ArrowLeft className="h-4 w-4" />
        返回博客列表
      </Link>

      {/* Article Header */}
      <article>
        <Badge variant="secondary">{MOCK_POST.category.name}</Badge>
        <h1 className="mt-3 text-3xl font-bold leading-tight">{MOCK_POST.title}</h1>
        <p className="mt-3 text-lg text-muted-foreground">{MOCK_POST.summary}</p>

        {/* Meta */}
        <div className="mt-6 flex flex-wrap items-center gap-4 border-y border-border py-4">
          <div className="flex items-center gap-2">
            <Avatar name="作者" size="sm" />
            <span className="text-sm font-medium">作者名称</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            {formatDateTime(MOCK_POST.created_at)}
          </div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Eye className="h-4 w-4" />
            {MOCK_POST.view_count} 浏览
          </div>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <MessageCircle className="h-4 w-4" />
            {MOCK_POST.comment_count} 评论
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={() => setIsFavorited(!isFavorited)}
            >
              <Bookmark className={cn('h-4 w-4', isFavorited && 'fill-primary text-primary')} />
              {isFavorited ? '已收藏' : '收藏'}
            </Button>
          </div>
        </div>

        {/* Cover Image */}
        <div className="mt-6 aspect-video rounded-lg bg-muted flex items-center justify-center">
          <span className="text-muted-foreground">封面图片占位</span>
        </div>

        {/* Content Placeholder */}
        <div className="mt-8 prose dark:prose-invert max-w-none">
          <div className="space-y-4 text-foreground">
            <h2 className="text-2xl font-bold">use() Hook</h2>
            <p className="leading-relaxed">
              React 19 引入了全新的 <code>use()</code> Hook，这是一个革命性的 API 设计。
              与传统的 Hooks 不同，<code>use()</code> 可以在条件语句、循环和 try-catch 块中使用，
              极大地提升了代码的灵活性。
            </p>
            <div className="rounded-lg bg-muted p-4 font-mono text-sm">
              <pre>function Component() {'{\n  // 可以在条件中使用！\n  '}if (condition) {'{\n    '}const data = use(promise);{'\n    return <div>{data}</div>;\n  }\n}'}</pre>
            </div>
            <h2 className="text-2xl font-bold">Server Components</h2>
            <p className="leading-relaxed">
              Server Components 是 React 架构的重要演进。它们仅在服务器端执行，
              不会被打包到客户端 bundle 中，从而显著减少前端代码体积。
            </p>
            <h2 className="text-2xl font-bold">Actions</h2>
            <p className="leading-relaxed">
              Actions 提供了一种声明式处理表单和数据变更的方式。
              配合 <code>useTransition</code> 和 <code>useActionState</code>，
              可以优雅地处理异步操作的状态管理。
            </p>
          </div>
        </div>

        {/* Tags */}
        <div className="mt-8 flex flex-wrap gap-2">
          {MOCK_POST.tags.map(tag => (
            <Badge key={tag} variant="outline">{tag}</Badge>
          ))}
        </div>
      </article>

      {/* Prev/Next Navigation */}
      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        {MOCK_POST.prev_post && (
          <Link to={`/blog/${MOCK_POST.prev_post.slug}`}>
            <Card className="h-full transition-colors hover:border-primary/50">
              <CardContent className="p-4">
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <ArrowLeft className="h-3 w-3" /> 上一篇
                </span>
                <p className="mt-1 font-medium line-clamp-2">{MOCK_POST.prev_post.title}</p>
              </CardContent>
            </Card>
          </Link>
        )}
        {MOCK_POST.next_post && (
          <Link to={`/blog/${MOCK_POST.next_post.slug}`}>
            <Card className="h-full transition-colors hover:border-primary/50">
              <CardContent className="p-4 text-right">
                <span className="text-xs text-muted-foreground flex items-center justify-end gap-1">
                  下一篇 <ArrowRight className="h-3 w-3" />
                </span>
                <p className="mt-1 font-medium line-clamp-2">{MOCK_POST.next_post.title}</p>
              </CardContent>
            </Card>
          </Link>
        )}
      </div>

      {/* Comments */}
      <div className="mt-10">
        <CommentSection targetType="blog_post" targetId={Number(MOCK_POST.id)} />
      </div>
    </div>
  )
}

