import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Filter, Clock, Eye, MessageCircle, Tag } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import Pagination from '@/components/ui/Pagination'
import { cn } from '@/lib/utils'

const MOCK_CATEGORIES = [
  { id: 1, name: '全部' },
  { id: 2, name: '前端开发' },
  { id: 3, name: '后端开发' },
  { id: 4, name: '数据库' },
  { id: 5, name: 'AI' },
  { id: 6, name: '运维' },
]

const MOCK_POSTS = [
  {
    id: 1,
    title: 'React 19 新特性详解：从 use 到 Server Components',
    slug: 'react-19-features',
    summary: 'React 19 带来了许多激动人心的新特性，包括 use() Hook、Server Components、Actions 等。本文将深入探讨这些特性如何改变我们构建应用的方式。',
    cover_image_url: null,
    category: { name: '前端开发' },
    tags: ['React', 'Frontend', 'JavaScript'],
    status: 'published',
    view_count: 1205,
    comment_count: 32,
    created_at: '2024-01-15T10:00:00',
  },
  {
    id: 2,
    title: 'FastAPI 性能优化指南：从入门到生产',
    slug: 'fastapi-performance',
    summary: 'FastAPI 是一个高性能的 Python Web 框架。本文将介绍如何优化 FastAPI 应用的性能，包括异步处理、数据库连接池、缓存策略等。',
    cover_image_url: null,
    category: { name: '后端开发' },
    tags: ['FastAPI', 'Python', 'Backend'],
    status: 'published',
    view_count: 892,
    comment_count: 18,
    created_at: '2024-01-14T08:30:00',
  },
  {
    id: 3,
    title: 'LangGraph 工作流设计模式实践',
    slug: 'langgraph-patterns',
    summary: 'LangGraph 是 LangChain 生态系统中的工作流编排工具。本文将介绍常见的工作流设计模式，以及如何在实际项目中应用。',
    cover_image_url: null,
    category: { name: 'AI' },
    tags: ['LangGraph', 'LangChain', 'AI'],
    status: 'published',
    view_count: 1567,
    comment_count: 45,
    created_at: '2024-01-13T14:00:00',
  },
  {
    id: 4,
    title: 'PostgreSQL 向量搜索实战：pgvector 入门',
    slug: 'pgvector-tutorial',
    summary: 'pgvector 是 PostgreSQL 的向量扩展，支持高效的相似度搜索。本文将介绍如何安装、配置和使用 pgvector 构建向量搜索应用。',
    cover_image_url: null,
    category: { name: '数据库' },
    tags: ['PostgreSQL', 'Vector', 'Database'],
    status: 'published',
    view_count: 743,
    comment_count: 12,
    created_at: '2024-01-12T09:00:00',
  },
]

export default function BlogListPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState(1)
  const [currentPage, setCurrentPage] = useState(1)

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold">博客</h1>
        <p className="mt-1 text-muted-foreground">技术文章、教程与分享</p>
      </div>

      {/* Search & Filter */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索文章..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">分类：</span>
        </div>
      </div>

      {/* Categories */}
      <div className="mb-8 flex flex-wrap gap-2">
        {MOCK_CATEGORIES.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={cn(
              'rounded-full px-4 py-1.5 text-sm font-medium transition-colors',
              selectedCategory === cat.id
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            )}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Posts Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MOCK_POSTS.map(post => (
          <Link key={post.id} to={`/blog/${post.slug}`}>
            <Card className="h-full transition-all hover:border-primary/50 hover:shadow-md overflow-hidden group">
              {/* Cover Placeholder */}
              <div className="aspect-video bg-muted flex items-center justify-center">
                <Tag className="h-8 w-8 text-muted-foreground/30" />
              </div>
              <CardContent className="p-5">
                <Badge variant="secondary" className="mb-2">{post.category.name}</Badge>
                <h3 className="font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                  {post.title}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
                  {post.summary}
                </p>
                <div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(post.created_at).toLocaleDateString('zh-CN')}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye className="h-3 w-3" />
                    {post.view_count}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageCircle className="h-3 w-3" />
                    {post.comment_count}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {post.tags.map(tag => (
                    <span key={tag} className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pagination */}
      <div className="mt-8 flex justify-center">
        <Pagination currentPage={currentPage} totalPages={5} onPageChange={setCurrentPage} />
      </div>
    </div>
  )
}
