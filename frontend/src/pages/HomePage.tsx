import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  BookOpen,
  MessageSquare,
  Briefcase,
  ArrowRight,
  Eye,
  MessageCircle,
  Clock,
  Flame,
  LayoutGrid,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { getBlogPostList } from '../api/blog'
import { getForumPostList, getForumZoneList } from '../api/forum'
import AppTopNav from '../components/AppTopNav'
import { useLogout } from '../hooks/useLogout'
import { useViewport } from '../hooks/useViewport'
import { formatDate } from '../utils/format'
import type { BlogPostListItem } from '../types/blog'
import type { ForumPostListItem, ForumZone } from '../types/forum'

/* ─── Types ─── */
interface HomeData {
  blogs: BlogPostListItem[]
  hotPosts: ForumPostListItem[]
  zones: ForumZone[]
}

/* ─── Sub-components ─── */

function HeroSection() {
  return (
    <section
      style={{
        backgroundColor: 'var(--color-canvas)',
        padding: 'var(--spacing-section) var(--spacing-xl)',
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--spacing-xxl)',
          alignItems: 'center',
        }}
      >
        {/* Left: Text */}
        <div>
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
              textTransform: 'uppercase' as const,
              color: 'var(--color-primary)',
              marginBottom: 'var(--spacing-lg)',
            }}
          >
            <Sparkles size={12} />
            Developer Space
          </div>

          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(48px, 6vw, 80px)',
              fontWeight: 400,
              lineHeight: 1.0,
              letterSpacing: '-2px',
              color: 'var(--color-ink)',
              margin: '0 0 var(--spacing-sm)',
            }}
          >
            DE hub
          </h1>

          <p
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(20px, 2.5vw, 28px)',
              fontWeight: 400,
              lineHeight: 1.2,
              letterSpacing: '-0.3px',
              color: 'var(--color-body-strong)',
              margin: '0 0 var(--spacing-md)',
            }}
          >
            开发者的个人空间站
          </p>

          <div
            style={{
              width: 48,
              height: 3,
              backgroundColor: 'var(--color-primary)',
              borderRadius: 'var(--rounded-pill)',
              marginBottom: 'var(--spacing-lg)',
            }}
          />

          <p
            style={{
              fontSize: 16,
              lineHeight: 1.6,
              color: 'var(--color-body)',
              maxWidth: 460,
              margin: '0 0 var(--spacing-xl)',
            }}
          >
            汇集技术博客、社区论坛与项目作品。记录学习思考，分享实战经验，与志同道合的开发者共同成长。
          </p>

          <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
            <a
              href="/blogs"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                height: 44,
                padding: '0 24px',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: 'var(--color-primary)',
                color: 'var(--color-on-primary)',
                fontSize: 14,
                fontWeight: 500,
                textDecoration: 'none',
                transition: 'background-color 150ms ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-primary)'
              }}
            >
              浏览博客
              <ArrowRight size={15} />
            </a>
            <a
              href="#forum"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                height: 44,
                padding: '0 24px',
                borderRadius: 'var(--rounded-md)',
                backgroundColor: 'var(--color-canvas)',
                color: 'var(--color-ink)',
                fontSize: 14,
                fontWeight: 500,
                textDecoration: 'none',
                border: '1px solid var(--color-hairline)',
                transition: 'background-color 150ms ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
              }}
            >
              加入论坛
            </a>
          </div>
        </div>

        {/* Right: Code mockup card */}
        <div
          style={{
            backgroundColor: 'var(--color-surface-dark)',
            borderRadius: 'var(--rounded-xl)',
            padding: 'var(--spacing-lg)',
            color: 'var(--color-on-dark)',
            fontFamily: 'var(--font-code)',
            fontSize: 14,
            lineHeight: 1.6,
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          {/* Window chrome */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 'var(--spacing-md)' }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#c64545' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#d4a017' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#5db872' }} />
            <span style={{ marginLeft: 'var(--spacing-sm)', fontSize: 12, color: 'var(--color-on-dark-soft)' }}>
              developer@dehub:~ — zsh
            </span>
          </div>

          <div style={{ color: 'var(--color-on-dark-soft)' }}>
            <span style={{ color: '#5db8a6' }}>➜</span> <span style={{ color: '#e8a55a' }}>~</span> cat about_me.md
          </div>
          <div style={{ marginTop: 'var(--spacing-sm)', color: '#a09d96' }}>
            # About Me
          </div>
          <div style={{ color: '#a09d96' }}>
            - Passionate about clean code & system design
          </div>
          <div style={{ color: '#a09d96' }}>
            - Building things with Python, TypeScript & React
          </div>
          <div style={{ color: '#a09d96' }}>
            - Exploring AI, LLMs and developer tools
          </div>
          <div style={{ color: '#a09d96' }}>
            - Open source enthusiast & lifelong learner
          </div>
          <div style={{ marginTop: 'var(--spacing-sm)', color: 'var(--color-on-dark-soft)' }}>
            <span style={{ color: '#5db8a6' }}>➜</span> <span style={{ color: '#e8a55a' }}>~</span>{' '}
            <span style={{ animation: 'blink 1s step-end infinite' }}>_</span>
          </div>

          <style>{`
            @keyframes blink {
              0%, 100% { opacity: 1; }
              50% { opacity: 0; }
            }
          `}</style>
        </div>
      </div>
    </section>
  )
}

function BlogCard({ blog }: { blog: BlogPostListItem }) {
  const navigate = useNavigate()
  return (
    <article
      onClick={() => navigate(`/blogs/${blog.slug}`)}
      style={{
        cursor: 'pointer',
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        padding: 'var(--spacing-xl)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-sm)',
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-xs)', marginBottom: 2 }}>
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
        {blog.tags.slice(0, 1).map((tag) => (
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
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Eye size={12} />
          {blog.view_count}
        </span>
      </div>
    </article>
  )
}

function BlogSection({ blogs }: { blogs: BlogPostListItem[] }) {
  const navigate = useNavigate()
  return (
    <section
      id="blogs"
      style={{
        backgroundColor: 'var(--color-surface-soft)',
        padding: 'var(--spacing-section) var(--spacing-xl)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 'var(--spacing-xl)', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
          <div>
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
                textTransform: 'uppercase' as const,
                color: 'var(--color-primary)',
                marginBottom: 'var(--spacing-md)',
              }}
            >
              <BookOpen size={12} />
              博客
            </div>
            <h2
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'clamp(28px, 3.5vw, 36px)',
                fontWeight: 400,
                lineHeight: 1.15,
                letterSpacing: '-0.5px',
                color: 'var(--color-ink)',
                margin: '0 0 var(--spacing-sm)',
              }}
            >
              最新文章
            </h2>
            <p style={{ fontSize: 16, lineHeight: 1.55, color: 'var(--color-muted)', margin: 0, maxWidth: 520 }}>
              技术探索、实战复盘与学习笔记，记录成长路上的每一步思考。
            </p>
          </div>
          <button
            onClick={() => navigate('/blogs')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '10px 20px',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              borderRadius: 'var(--rounded-md)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              transition: 'background-color 150ms ease',
              flexShrink: 0,
              height: 40,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-primary)'
            }}
          >
            查看全部
            <ArrowRight size={14} />
          </button>
        </div>

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
      </div>
    </section>
  )
}

function ForumSection({ posts, zones }: { posts: ForumPostListItem[]; zones: ForumZone[] }) {
  const navigate = useNavigate()
  const isMobile = useViewport() < 768
  return (
    <section
      id="forum"
      style={{
        backgroundColor: 'var(--color-canvas)',
        padding: isMobile
          ? 'var(--spacing-xxl) var(--spacing-lg)'
          : 'var(--spacing-section) var(--spacing-xl)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 'var(--spacing-xl)' }}>
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
              textTransform: 'uppercase' as const,
              color: 'var(--color-primary)',
              marginBottom: 'var(--spacing-md)',
            }}
          >
            <MessageSquare size={12} />
            论坛
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(28px, 3.5vw, 36px)',
              fontWeight: 400,
              lineHeight: 1.15,
              letterSpacing: '-0.5px',
              color: 'var(--color-ink)',
              margin: '0 0 var(--spacing-sm)',
            }}
          >
            社区动态
          </h2>
          <p style={{ fontSize: 16, lineHeight: 1.55, color: 'var(--color-muted)', margin: 0, maxWidth: 520 }}>
            与技术同好交流讨论，分享经验、解决问题、共同进步。
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? 'minmax(0, 1fr)' : '300px minmax(0, 1fr)',
            gap: isMobile ? 'var(--spacing-lg)' : 'var(--spacing-xl)',
          }}
        >
          {/* Left: Zones */}
          <div
            style={{
              backgroundColor: 'var(--color-surface-card)',
              borderRadius: 'var(--rounded-lg)',
              padding: isMobile ? 'var(--spacing-lg)' : 'var(--spacing-xl)',
              height: 'fit-content',
              minWidth: 0,
            }}
          >
            <h3
              style={{
                fontSize: 16,
                fontWeight: 500,
                color: 'var(--color-ink)',
                margin: '0 0 var(--spacing-md)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <LayoutGrid size={16} color="var(--color-primary)" />
              热门分区
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
              {zones.slice(0, 8).map((zone) => (
                <div
                  key={zone.id}
                  onClick={() => navigate(`/forums/z/${zone.slug}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 12px',
                    borderRadius: 'var(--rounded-md)',
                    cursor: 'pointer',
                    transition: 'background-color 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-body)' }}>
                    {zone.zone_name}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--color-muted-soft)' }}>
                    {zone.view_count} 浏览
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Hot posts */}
          <div
            style={{
              backgroundColor: 'var(--color-surface-card)',
              borderRadius: 'var(--rounded-lg)',
              padding: isMobile ? 'var(--spacing-lg)' : 'var(--spacing-xl)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--spacing-sm)',
              minWidth: 0,
            }}
          >
            <h3
              style={{
                fontSize: 16,
                fontWeight: 500,
                color: 'var(--color-ink)',
                margin: '0 0 var(--spacing-sm)',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Flame size={16} color="var(--color-primary)" />
              热门帖子
            </h3>
            {posts.map((post, idx) => (
              <div
                key={post.id}
                onClick={() => navigate(`/forums/p/${post.id}`)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--spacing-md)',
                  padding: '14px 16px',
                  borderRadius: 'var(--rounded-md)',
                  cursor: 'pointer',
                  transition: 'background-color 150ms ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}
              >
                <span
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: idx < 3 ? 'var(--color-primary)' : 'var(--color-muted-soft)',
                    width: 24,
                    textAlign: 'center',
                    flexShrink: 0,
                  }}
                >
                  {idx + 1}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 15,
                      fontWeight: 500,
                      color: 'var(--color-body-strong)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {post.title}
                  </div>
                  <div
                    style={{
                      fontSize: 13,
                      color: 'var(--color-muted-soft)',
                      marginTop: 2,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--spacing-sm)',
                    }}
                  >
                    <span>{post.user.username}</span>
                    <span>·</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Eye size={12} />
                      {post.view_count}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                      <MessageCircle size={12} />
                      {post.reply_count}
                    </span>
                  </div>
                </div>
                <ChevronRight size={16} color="var(--color-muted-soft)" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function PortfolioSection() {
  return (
    <section
      id="portfolio"
      style={{
        backgroundColor: 'var(--color-surface-soft)',
        padding: 'var(--spacing-section) var(--spacing-xl)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div
          style={{
            backgroundColor: 'var(--color-primary)',
            borderRadius: 'var(--rounded-lg)',
            padding: 'clamp(40px, 5vw, 64px)',
            color: 'var(--color-on-primary)',
            textAlign: 'center',
          }}
        >
          <Briefcase size={32} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.9 }} />
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'clamp(24px, 3vw, 28px)',
              fontWeight: 400,
              lineHeight: 1.2,
              letterSpacing: '-0.3px',
              margin: '0 0 var(--spacing-sm)',
            }}
          >
            探索作品集
          </h2>
          <p
            style={{
              fontSize: 16,
              lineHeight: 1.55,
              opacity: 0.85,
              maxWidth: 480,
              margin: '0 auto var(--spacing-xl)',
            }}
          >
            汇集了我的开源项目、技术实验与创意作品，每一个项目都是一次新的探索。
          </p>
          <button
            onClick={() => toast.info('作品集页面即将开放，敬请期待！')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              height: 44,
              padding: '0 24px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: 'var(--color-canvas)',
              color: 'var(--color-ink)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
              transition: 'background-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-cream-strong)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
            }}
          >
            查看作品
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </section>
  )
}

function FooterSection() {
  return (
    <footer
      style={{
        backgroundColor: 'var(--color-surface-dark)',
        color: 'var(--color-on-dark-soft)',
        padding: '64px var(--spacing-xl)',
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--spacing-xl)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 'var(--spacing-md)' }}>
            <Sparkles size={18} color="var(--color-primary)" />
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 18,
                fontWeight: 500,
                color: 'var(--color-on-dark)',
              }}
            >
              DE hub
            </span>
          </div>
          <p style={{ fontSize: 14, lineHeight: 1.55, margin: 0 }}>
            开发者的个人空间站，记录思考、分享技术、构建连接。
          </p>
        </div>

        <div>
          <h4 style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-on-dark)', margin: '0 0 var(--spacing-md)', letterSpacing: '1px', textTransform: 'uppercase' as const }}>
            导航
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {['博客', '论坛', '作品集'].map((item) => (
              <span key={item} style={{ fontSize: 14, color: 'var(--color-on-dark-soft)' }}>
                {item}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h4 style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-on-dark)', margin: '0 0 var(--spacing-md)', letterSpacing: '1px', textTransform: 'uppercase' as const }}>
            关于
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {['开发者介绍', '技术栈', '更新日志'].map((item) => (
              <span key={item} style={{ fontSize: 14, color: 'var(--color-on-dark-soft)' }}>
                {item}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h4 style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-on-dark)', margin: '0 0 var(--spacing-md)', letterSpacing: '1px', textTransform: 'uppercase' as const }}>
            声明
          </h4>
          <p style={{ fontSize: 13, lineHeight: 1.6, margin: 0 }}>
            本站内容为个人学习与技术分享，不代表任何组织或公司观点。如有问题，欢迎通过论坛交流反馈。
          </p>
        </div>
      </div>

      <div
        style={{
          maxWidth: 1200,
          margin: 'var(--spacing-xl) auto 0',
          paddingTop: 'var(--spacing-lg)',
          borderTop: '1px solid var(--color-surface-dark-elevated)',
          fontSize: 13,
          color: 'var(--color-on-dark-soft)',
          textAlign: 'center',
        }}
      >
        © {new Date().getFullYear()} DE hub. All rights reserved. Built with passion.
      </div>
    </footer>
  )
}

/* ─── Main Page ─── */

export default function HomePage() {
  const vw = useViewport()
  const isMobile = vw < 768

  const [data, setData] = useState<HomeData>({ blogs: [], hotPosts: [], zones: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const [blogRes, postRes, zoneRes] = await Promise.all([
        getBlogPostList({ limit: 6, status: 'published' }),
        getForumPostList({ limit: 6, sort_by: 'view' }),
        getForumZoneList(),
      ])
      setData({
        blogs: blogRes.data.items || [],
        hotPosts: postRes.data.items || [],
        zones: zoneRes.data || [],
      })
    } catch {
      setError('数据加载失败，请刷新页面重试')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleLogout = useLogout()

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-canvas)' }}>
      <AppTopNav onLogout={handleLogout} forumHref="/forums" />

      <HeroSection />

      {loading ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-section)',
            gap: 'var(--spacing-md)',
            color: 'var(--color-muted)',
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              border: '3px solid var(--color-hairline)',
              borderTopColor: 'var(--color-primary)',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
            }}
          />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          <span style={{ fontSize: 14 }}>正在加载内容…</span>
        </div>
      ) : error ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-section)',
            gap: 'var(--spacing-md)',
            color: 'var(--color-error)',
          }}
        >
          <p style={{ fontSize: 14 }}>{error}</p>
          <button
            onClick={fetchData}
            style={{
              height: 36,
              padding: '0 16px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              fontSize: 13,
              fontWeight: 500,
              border: 'none',
              cursor: 'pointer',
            }}
          >
            重新加载
          </button>
        </div>
      ) : (
        <>
          {data.blogs.length > 0 && <BlogSection blogs={data.blogs} />}
          {(data.hotPosts.length > 0 || data.zones.length > 0) && (
            <ForumSection posts={data.hotPosts} zones={data.zones} />
          )}
        </>
      )}

      <PortfolioSection />
      <FooterSection />

      {/* Mobile responsive override for forum grid */}
      {isMobile && (
        <style>{`
          #forum > div > div:last-child {
            grid-template-columns: 1fr !important;
          }
        `}</style>
      )}
    </div>
  )
}
