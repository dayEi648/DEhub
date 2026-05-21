import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen,
  Search,
  Eye,
  MessageCircle,
  Clock,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  LogOut,
  User,
  Settings,
} from 'lucide-react'
import { getBlogPostList, getBlogCategories } from '../api/blog'
import { logout } from '../api/users'
import { clearAuth, getUser } from '../utils/auth'
import type { BlogPostListItem, BlogCategoryWithPostCount } from '../types/blog'

/* ─── Helpers ─── */
function formatDate(iso: string): string {
  const d = new Date(iso)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}

const PAGE_SIZE = 12

/* ─── TopNav ─── */
function TopNav({ onLogout }: { onLogout: () => void }) {
  const currentUser = getUser()
  const navigate = useNavigate()

  const navLinks = [
    { label: '博客', href: '/blogs' },
    { label: '论坛', href: '/#forum' },
    { label: '作品集', href: '/#portfolio' },
  ]

  const linkStyle: React.CSSProperties = {
    fontSize: 14,
    fontWeight: 500,
    color: 'var(--color-ink)',
    textDecoration: 'none',
    lineHeight: 1.4,
    transition: 'color 150ms ease',
  }

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        height: 64,
        backgroundColor: 'var(--color-canvas)',
        borderBottom: '1px solid var(--color-hairline-soft)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--spacing-xl)',
      }}
    >
      {/* Logo */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', cursor: 'pointer' }}
        onClick={() => navigate('/')}
      >
        <Sparkles size={20} color="var(--color-primary)" />
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 20,
            fontWeight: 500,
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
          }}
        >
          DE hub
        </span>
      </div>

      {/* Center Nav */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
        {navLinks.map((l) => (
          <a
            key={l.label}
            href={l.href}
            style={linkStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-primary)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-ink)'
            }}
          >
            {l.label}
          </a>
        ))}
      </nav>

      {/* Right cluster */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
        <button
          onClick={() => navigate('/admin/logs')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-muted)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            transition: 'color 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--color-ink)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--color-muted)'
          }}
        >
          <Settings size={15} />
          管理后台
        </button>

        {currentUser && (
          <button
            onClick={() => navigate('/profile')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: 'var(--rounded-md)',
              transition: 'background-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--rounded-full)',
                backgroundColor: 'var(--color-surface-card)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
              }}
            >
              <User size={14} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-body-strong)' }}>
              {currentUser.username}
            </span>
          </button>
        )}

        <button
          onClick={onLogout}
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--rounded-full)',
            backgroundColor: 'var(--color-canvas)',
            border: '1px solid var(--color-hairline)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-ink)',
            cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-card)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
          }}
          title="登出"
        >
          <LogOut size={15} />
        </button>
      </div>
    </header>
  )
}

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
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        transition: 'transform 150ms ease, box-shadow 150ms ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(20,20,19,0.06)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'none'
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

/* ─── Pagination ─── */
function Pagination({
  current,
  total,
  onChange,
}: {
  current: number
  total: number
  onChange: (page: number) => void
}) {
  if (total <= 1) return null

  const pages: (number | string)[] = []
  const maxVisible = 5

  if (total <= maxVisible + 2) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--spacing-xs)', marginTop: 'var(--spacing-xl)' }}>
      <button
        onClick={() => onChange(current - 1)}
        disabled={current === 1}
        style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: current === 1 ? 'not-allowed' : 'pointer',
          opacity: current === 1 ? 0.5 : 1,
          color: 'var(--color-ink)',
          transition: 'all 150ms ease',
        }}
      >
        <ChevronLeft size={16} />
      </button>

      {pages.map((p, idx) =>
        p === '...' ? (
          <span key={`dot-${idx}`} style={{ padding: '0 8px', color: 'var(--color-muted-soft)', fontSize: 14 }}>
            ...
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p as number)}
            style={{
              minWidth: 36,
              height: 36,
              borderRadius: 'var(--rounded-md)',
              border: '1px solid',
              borderColor: current === p ? 'var(--color-primary)' : 'var(--color-hairline)',
              backgroundColor: current === p ? 'var(--color-primary)' : 'var(--color-canvas)',
              color: current === p ? 'var(--color-on-primary)' : 'var(--color-ink)',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 150ms ease',
            }}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => onChange(current + 1)}
        disabled={current === total}
        style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: current === total ? 'not-allowed' : 'pointer',
          opacity: current === total ? 0.5 : 1,
          color: 'var(--color-ink)',
          transition: 'all 150ms ease',
        }}
      >
        <ChevronRight size={16} />
      </button>
    </div>
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
export default function BlogListPage() {
  const navigate = useNavigate()
  const [blogs, setBlogs] = useState<BlogPostListItem[]>([])
  const [categories, setCategories] = useState<BlogCategoryWithPostCount[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [activeSearch, setActiveSearch] = useState('')
  const [activeCategory, setActiveCategory] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
      })
      setBlogs(res.data.items)
      setTotal(res.data.total)
    } catch {
      setError('加载文章失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [page, activeSearch, activeCategory])

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

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      await logout(refreshToken ? { refresh_token: refreshToken } : {})
    } catch {
      // ignore
    } finally {
      clearAuth()
      navigate('/login', { replace: true })
    }
  }

  const handleSearch = () => {
    setActiveSearch(search)
    setPage(1)
  }

  const handleCategoryChange = (id: number | null) => {
    setActiveCategory(id)
    setPage(1)
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      <TopNav onLogout={handleLogout} />
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
          {loading ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-muted)' }}>
              加载中...
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-error)' }}>
              {error}
            </div>
          ) : blogs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-muted)' }}>
              <BookOpen size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.3 }} />
              <p style={{ fontSize: 16, margin: 0 }}>暂无文章</p>
              <p style={{ fontSize: 14, color: 'var(--color-muted-soft)', marginTop: 'var(--spacing-xs)' }}>
                {activeSearch || activeCategory ? '尝试切换筛选条件' : '敬请期待'}
              </p>
            </div>
          ) : (
            <>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                  gap: 'var(--spacing-lg)',
                }}
              >
                {blogs.map((blog) => (
                  <BlogCard key={blog.id} blog={blog} />
                ))}
              </div>
              <Pagination current={page} total={totalPages} onChange={setPage} />
            </>
          )}
        </div>
      </section>

      <Footer />
    </div>
  )
}
