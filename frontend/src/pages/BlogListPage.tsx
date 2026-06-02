import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen,
  Search,
  Eye,
  MessageCircle,
  Clock,
  User,
  Plus,
} from 'lucide-react'
import { toast } from 'sonner'
import {
  getBlogPostList,
  getBlogCategories,
  createBlogPost,
  createBlogCategory,
} from '../api/blog'
import { getUser } from '../utils/auth'
import { isAuthError } from '../utils/error'
import BlogEditorModal from '../components/BlogEditorModal'
import BaseModal from '../components/BaseModal'
import AppTopNav from '../components/AppTopNav'
import Footer from '../components/Footer'
import Pagination from '../components/Pagination'
import StaggerChildren from '../components/ui/StaggerChildren'
import { Skeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import { useLogout } from '../hooks/useLogout'
import { formatDate } from '../utils/format'
import type { BlogPostListItem, BlogCategoryWithPostCount } from '../types/blog'

const PAGE_SIZE = 12

/* ─── Hero ─── */
function HeroSection() {
  return (
    <section
      style={{
        backgroundColor: 'var(--color-canvas)',
        padding: 'var(--spacing-section) var(--spacing-xl)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 12px',
            borderRadius: 'var(--rounded-pill)',
            backgroundColor: 'var(--color-surface-card)',
            fontSize: 12,
            fontWeight: 500,
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            color: 'var(--color-primary)',
            marginBottom: 'var(--spacing-md)',
          }}
        >
          <BookOpen size={12} />
          博客
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(36px, 5vw, 64px)',
            fontWeight: 400,
            lineHeight: 1.05,
            letterSpacing: '-1.5px',
            color: 'var(--color-ink)',
            margin: '0 0 var(--spacing-sm)',
          }}
        >
          探索与思考
        </h1>
        <p
          style={{
            fontSize: 18,
            lineHeight: 1.55,
            color: 'var(--color-muted)',
            margin: 0,
            maxWidth: 560,
          }}
        >
          技术博客、实战复盘与学习笔记。在这里记录成长，分享经验，与志同道合的开发者一起进步。
        </p>
      </div>
    </section>
  )
}

/* ─── Search + Filter ─── */
function FilterBar({
  categories,
  activeCategory,
  onCategoryChange,
  searchValue,
  onSearchChange,
  onSearch,
}: {
  categories: BlogCategoryWithPostCount[]
  activeCategory: number | null
  onCategoryChange: (id: number | null) => void
  searchValue: string
  onSearchChange: (v: string) => void
  onSearch: () => void
}) {
  return (
    <section
      style={{
        backgroundColor: 'var(--color-surface-soft)',
        padding: 'var(--spacing-xl) var(--spacing-xl)',
        borderBottom: '1px solid var(--color-hairline-soft)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* Search */}
        <div
          style={{
            display: 'flex',
            gap: 'var(--spacing-sm)',
            marginBottom: 'var(--spacing-lg)',
            maxWidth: 480,
          }}
        >
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline)',
              borderRadius: 'var(--rounded-md)',
              padding: '0 var(--spacing-md)',
              height: 44,
            }}
          >
            <Search size={16} color="var(--color-muted-soft)" />
            <input
              type="text"
              placeholder="搜索文章标题..."
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onSearch()
              }}
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                fontSize: 14,
                color: 'var(--color-ink)',
                outline: 'none',
              }}
            />
          </div>
          <button
            onClick={onSearch}
            style={{
              height: 44,
              padding: '0 var(--spacing-lg)',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              transition: 'background-color 150ms ease',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-primary)'
            }}
          >
            <Search size={14} />
            搜索
          </button>
        </div>

        {/* Category tabs */}
        <div style={{ display: 'flex', gap: 'var(--spacing-xs)', flexWrap: 'wrap' }}>
          <button
            onClick={() => onCategoryChange(null)}
            style={{
              padding: '8px 14px',
              borderRadius: 'var(--rounded-md)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              backgroundColor: activeCategory === null ? 'var(--color-surface-card)' : 'transparent',
              color: activeCategory === null ? 'var(--color-ink)' : 'var(--color-muted)',
            }}
          >
            全部
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => onCategoryChange(cat.id)}
              style={{
                padding: '8px 14px',
                borderRadius: 'var(--rounded-md)',
                fontSize: 14,
                fontWeight: 500,
                border: 'none',
                cursor: 'pointer',
                transition: 'all 150ms ease',
                backgroundColor: activeCategory === cat.id ? 'var(--color-surface-card)' : 'transparent',
                color: activeCategory === cat.id ? 'var(--color-ink)' : 'var(--color-muted)',
              }}
            >
              {cat.name}
              <span
                style={{
                  marginLeft: 4,
                  fontSize: 12,
                  color: 'var(--color-muted-soft)',
                }}
              >
                ({cat.post_count})
              </span>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ─── Blog Card ─── */
function BlogCard({ blog }: { blog: BlogPostListItem }) {
  const navigate = useNavigate()

  return (
    <article
      onClick={() => navigate(`/blogs/${blog.slug}`)}
      className="card-lift"
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
      }}
    >
      {/* Cover image */}
      <div
        style={{
          width: '100%',
          height: 180,
          backgroundColor: 'var(--color-surface-cream-strong)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {blog.cover_image_url ? (
          <img
            src={blog.cover_image_url}
            alt={blog.title}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transition: 'transform 300ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.03)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)'
            }}
          />
        ) : (
          <div
            style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-muted-soft)',
            }}
          >
            <BookOpen size={32} />
          </div>
        )}
      </div>

      {/* Content */}
      <div style={{ padding: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-xs)', flexWrap: 'wrap' }}>
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
              color: 'var(--color-ink)',
            }}
          >
            <BookOpen size={12} />
            {blog.category.name}
          </span>
          {blog.status === 'draft' && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: '4px 12px',
                borderRadius: 'var(--rounded-pill)',
                backgroundColor: 'var(--color-warning)',
                fontSize: 12,
                fontWeight: 500,
                color: '#fff',
              }}
            >
              草稿
            </span>
          )}
          {blog.tags.slice(0, 2).map((tag) => (
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

        <h3
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 20,
            fontWeight: 400,
            lineHeight: 1.2,
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
            margin: 0,
          }}
        >
          {blog.title}
        </h3>

        <p
          style={{
            fontSize: 14,
            lineHeight: 1.55,
            color: 'var(--color-muted)',
            margin: 0,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical' as const,
            overflow: 'hidden',
          }}
        >
          {blog.summary || '暂无摘要'}
        </p>

        <div
          style={{
            marginTop: 'auto',
            paddingTop: 'var(--spacing-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 13,
            color: 'var(--color-muted-soft)',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Clock size={12} />
            {formatDate(blog.created_at)}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <User size={12} />
              {blog.author.username}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Eye size={12} />
              {blog.view_count}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <MessageCircle size={12} />
              {blog.comment_count}
            </span>
          </span>
        </div>
      </div>
    </article>
  )
}

function CategoryCreateModal({
  submitting,
  onClose,
  onSubmit,
}: {
  submitting: boolean
  onClose: () => void
  onSubmit: (data: { name: string; slug: string; description: string }) => void
}) {
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')

  const inputStyle: React.CSSProperties = {
    width: '100%',
    height: 40,
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
  }

  const handleSubmit = () => {
    if (!name.trim()) return
    onSubmit({ name: name.trim(), slug: slug.trim(), description: description.trim() })
  }

  return (
    <BaseModal
      title={<h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 500, margin: 0 }}>创建博客分类</h2>}
      onClose={onClose}
      maxWidth={480}
      showCloseButton={false}
      footer={
        <>
          <button
            onClick={onClose}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: 'var(--color-canvas)',
              color: 'var(--color-ink)',
              border: '1px solid var(--color-hairline)',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || !name.trim()}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: submitting ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              border: 'none',
              fontSize: 14,
              fontWeight: 500,
              cursor: submitting || !name.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? '创建中…' : '创建'}
          </button>
        </>
      }
    >
      <div style={{ padding: 'var(--spacing-xl)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <div>
            <label style={modalLabelStyle}>分类名称 *</label>
            <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：工程实践" />
          </div>
          <div>
            <label style={modalLabelStyle}>Slug</label>
            <input style={inputStyle} value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="留空自动生成" />
          </div>
          <div>
            <label style={modalLabelStyle}>描述</label>
            <textarea
              style={{ ...inputStyle, height: 96, resize: 'vertical', fontFamily: 'var(--font-body)' }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="分类说明"
            />
          </div>
        </div>
    </BaseModal>
  )
}

const modalLabelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  fontWeight: 500,
  color: 'var(--color-muted)',
  marginBottom: 'var(--spacing-xs)',
  textTransform: 'uppercase',
  letterSpacing: '1px',
}

/* ─── Main Page ─── */
export default function BlogListPage() {
  const [blogs, setBlogs] = useState<BlogPostListItem[]>([])
  const [categories, setCategories] = useState<BlogCategoryWithPostCount[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [activeSearch, setActiveSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showEditor, setShowEditor] = useState(false)
  const [showCategoryEditor, setShowCategoryEditor] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [categorySubmitting, setCategorySubmitting] = useState(false)
  const currentUser = getUser()
  const isSuperAdmin = currentUser?.permission === 2

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const fetchBlogs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getBlogPostList({
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        q: activeSearch || undefined,
        category_id: activeCategory ?? undefined,
        include_unpublished: isSuperAdmin ? true : undefined,
      })
      setBlogs(res.data.items)
      setTotal(res.data.total)
    } catch (error) {
      if (!isAuthError(error)) {
        setError('加载文章失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }, [page, activeSearch, activeCategory, isSuperAdmin])

  const fetchCategories = useCallback(async () => {
    try {
      const res = await getBlogCategories()
      setCategories(res.data)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    fetchBlogs()
  }, [fetchBlogs])

  useEffect(() => {
    fetchCategories()
  }, [fetchCategories])

  const handleLogout = useLogout()

  const handleSearch = () => {
    setActiveSearch(search)
    setPage(1)
  }

  const handleCategoryChange = (id: number | null) => {
    setActiveCategory(id)
    setPage(1)
  }

  const handleCreateBlog = async (data: Parameters<typeof createBlogPost>[0] & { file?: File }) => {
    setSubmitting(true)
    try {
      await createBlogPost(data, data.file!)
      toast.success('文章创建成功')
      setShowEditor(false)
      fetchBlogs()
    } catch {
      toast.error('文章创建失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateCategory = async (data: { name: string; slug: string; description: string }) => {
    setCategorySubmitting(true)
    try {
      await createBlogCategory({
        name: data.name,
        slug: data.slug || undefined,
        description: data.description || undefined,
      })
      toast.success('分类创建成功')
      setShowCategoryEditor(false)
      fetchCategories()
    } catch {
      toast.error('分类创建失败')
    } finally {
      setCategorySubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      <AppTopNav onLogout={handleLogout} />
      <HeroSection />
      <FilterBar
        categories={categories}
        activeCategory={activeCategory}
        onCategoryChange={handleCategoryChange}
        searchValue={search}
        onSearchChange={setSearch}
        onSearch={handleSearch}
      />

      {/* Blog Grid */}
      <section style={{ flex: 1, padding: 'var(--spacing-xl) var(--spacing-xl)', backgroundColor: 'var(--color-canvas)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {isSuperAdmin && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
              <button
                onClick={() => setShowCategoryEditor(true)}
                style={{
                  height: 40,
                  padding: '0 18px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-surface-card)',
                  color: 'var(--color-ink)',
                  fontSize: 14,
                  fontWeight: 500,
                  border: '1px solid var(--color-hairline)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <Plus size={14} />
                创建分类
              </button>
              <button
                onClick={() => setShowEditor(true)}
                style={{
                  height: 40,
                  padding: '0 18px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-primary)',
                  color: 'var(--color-on-primary)',
                  fontSize: 14,
                  fontWeight: 500,
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <Plus size={14} />
                新建文章
              </button>
            </div>
          )}
          {loading ? (
            <Skeleton.CardGrid count={6} />
          ) : error ? (
            <ErrorState title="加载文章失败" description={error} onRetry={fetchBlogs} />
          ) : blogs.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="暂无文章"
              description={activeSearch || activeCategory ? '尝试切换筛选条件' : '敬请期待'}
              action={
                isSuperAdmin
                  ? { label: '新建文章', onClick: () => setShowEditor(true) }
                  : undefined
              }
            />
          ) : (
            <>
              <StaggerChildren
                animation="fadeInUp"
                staggerDelay={0.06}
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                  gap: 'var(--spacing-lg)',
                }}
              >
                {blogs.map((blog) => (
                  <BlogCard key={blog.id} blog={blog} />
                ))}
              </StaggerChildren>
              <Pagination current={page} total={totalPages} onChange={setPage} />
            </>
          )}
        </div>
      </section>

      <Footer />

      {showEditor && (
        <BlogEditorModal
          post={null}
          categories={categories}
          onClose={() => setShowEditor(false)}
          onSubmit={handleCreateBlog}
          submitting={submitting}
        />
      )}

      {showCategoryEditor && (
        <CategoryCreateModal
          submitting={categorySubmitting}
          onClose={() => setShowCategoryEditor(false)}
          onSubmit={handleCreateCategory}
        />
      )}
    </div>
  )
}
