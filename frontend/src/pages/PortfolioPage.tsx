import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import {
  ArrowLeft,
  Brain,
  Briefcase,
  FolderCode,
  Globe,
  Layers,
  Sparkles,
  Zap,
} from 'lucide-react'
import AppTopNav from '../components/AppTopNav'
import StaggerChildren from '../components/ui/StaggerChildren'
import EmptyState from '../components/ui/EmptyState'
import { useLogout } from '../hooks/useLogout'
import { getProjects } from '../data/projects'
import type { Project } from '../data/projects'

/* ─── Icon mapping ─── */
const iconMap: Record<string, React.ElementType> = {
  Brain,
  Briefcase,
  FolderCode,
  Globe,
  Layers,
  Sparkles,
  Zap,
}

function ProjectCard({ project }: { project: Project }) {
  const Icon = iconMap[project.coverIcon] || Sparkles

  return (
    <div
      onClick={() => toast.info('正在开发中')}
      className="card-lift-strong"
      style={{
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
    >
      {/* Cover */}
      <div
        style={{
          height: 180,
          background: project.coverGradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        <Icon size={48} color="rgba(255,255,255,0.9)" strokeWidth={1.2} />
        <div
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 28,
            height: 28,
            borderRadius: '50%',
            backgroundColor: 'rgba(255,255,255,0.15)',
            backdropFilter: 'blur(4px)',
          }}
        >
          <Sparkles size={14} color="rgba(255,255,255,0.9)" />
        </div>
      </div>

      {/* Content */}
      <div
        style={{
          padding: 'var(--spacing-xl)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-sm)',
          flex: 1,
        }}
      >
        <h3
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 20,
            fontWeight: 500,
            lineHeight: 1.25,
            color: 'var(--color-ink)',
            margin: 0,
          }}
        >
          {project.name}
        </h3>

        <p
          style={{
            fontSize: 14,
            lineHeight: 1.6,
            color: 'var(--color-muted)',
            margin: 0,
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical' as const,
            overflow: 'hidden',
            flex: 1,
          }}
        >
          {project.summary}
        </p>

        {/* Tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 'var(--spacing-xs)' }}>
          {project.tags.map((tag) => (
            <span
              key={tag}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '4px 10px',
                borderRadius: 'var(--rounded-pill)',
                backgroundColor: 'var(--color-canvas)',
                fontSize: 12,
                fontWeight: 500,
                color: 'var(--color-body-strong)',
                border: '1px solid var(--color-hairline)',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function PortfolioPage() {
  const navigate = useNavigate()
  const handleLogout = useLogout()
  const projectList = getProjects()

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-canvas)' }}>
      <AppTopNav onLogout={handleLogout} />

      <main
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: 'var(--spacing-xl)',
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: 'var(--spacing-xxl)' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 14px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: 'transparent',
              border: '1px solid var(--color-hairline)',
              color: 'var(--color-body)',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              marginBottom: 'var(--spacing-lg)',
              transition: 'background-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
          >
            <ArrowLeft size={14} />
            返回首页
          </button>

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
            <Briefcase size={12} />
            作品集
          </div>

          <h1
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
            项目作品
          </h1>

          <p
            style={{
              fontSize: 16,
              lineHeight: 1.55,
              color: 'var(--color-muted)',
              margin: 0,
              maxWidth: 560,
            }}
          >
            汇集开源项目、技术实验与创意作品。每个项目都是一次新的探索与实践。
          </p>
        </div>

        {/* Grid */}
        {projectList.length === 0 ? (
          <EmptyState icon={FolderCode} title="暂无项目展示" description="敬请期待" />
        ) : (
          <StaggerChildren
            animation="fadeInUp"
            staggerDelay={0.1}
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: 'var(--spacing-xl)',
            }}
          >
            {projectList.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </StaggerChildren>
        )}
      </main>
    </div>
  )
}
