import React from 'react'

/* ─── Base Skeleton Block ─── */
function SkeletonBlock({
  width,
  height,
  className = '',
  style,
}: {
  width?: string | number
  height?: string | number
  className?: string
  style?: React.CSSProperties
}) {
  return (
    <div
      className={`skeleton-shimmer ${className}`}
      style={{
        width: width ?? '100%',
        height: height ?? '1em',
        ...style,
      }}
    />
  )
}

/* ─── Card Skeleton (for BlogCard, ZoneCard, ProjectCard) ─── */
function Card({ className = '' }: { className?: string }) {
  return (
    <div
      className={`card-lift ${className}`}
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <SkeletonBlock height={180} style={{ borderRadius: 0 }} />
      <div style={{ padding: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
        <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
          <SkeletonBlock width={80} height={24} style={{ borderRadius: 'var(--rounded-pill)' }} />
          <SkeletonBlock width={60} height={24} style={{ borderRadius: 'var(--rounded-pill)' }} />
        </div>
        <SkeletonBlock width="85%" height={22} />
        <SkeletonBlock width="100%" height={14} />
        <SkeletonBlock width="70%" height={14} />
        <div style={{ marginTop: 'auto', paddingTop: 'var(--spacing-sm)', display: 'flex', justifyContent: 'space-between' }}>
          <SkeletonBlock width={100} height={14} />
          <SkeletonBlock width={80} height={14} />
        </div>
      </div>
    </div>
  )
}

/* ─── Card Grid Skeleton ─── */
function CardGrid({ count = 6 }: { count?: number }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: 'var(--spacing-lg)',
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className={`delay-${Math.min(i + 1, 6)}`} />
      ))}
    </div>
  )
}

/* ─── List Item Skeleton (for Forum Post List) ─── */
function ListItem() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-md)',
        padding: 'var(--spacing-md) var(--spacing-lg)',
        borderBottom: '1px solid var(--color-hairline-soft)',
      }}
    >
      <SkeletonBlock width={40} height={40} style={{ borderRadius: '50%', flexShrink: 0 }} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
        <SkeletonBlock width="70%" height={16} />
        <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
          <SkeletonBlock width={80} height={12} />
          <SkeletonBlock width={60} height={12} />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexShrink: 0 }}>
        <SkeletonBlock width={40} height={14} />
        <SkeletonBlock width={40} height={14} />
      </div>
    </div>
  )
}

/* ─── List Skeleton ─── */
function List({ count = 8 }: { count?: number }) {
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        overflow: 'hidden',
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <ListItem key={i} />
      ))}
    </div>
  )
}

/* ─── Text Skeleton (for paragraphs) ─── */
function Text({ lines = 3 }: { lines?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', width: '100%' }}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBlock
          key={i}
          width={i === lines - 1 ? '60%' : '100%'}
          height={14}
        />
      ))}
    </div>
  )
}

/* ─── Avatar Skeleton ─── */
function Avatar({ size = 40 }: { size?: number }) {
  return (
    <SkeletonBlock
      width={size}
      height={size}
      style={{ borderRadius: '50%', flexShrink: 0 }}
    />
  )
}

/* ─── Chat Bubble Skeleton ─── */
function ChatBubble({ isUser = false }: { isUser?: boolean }) {
  return (
    <div
      style={{
        alignSelf: isUser ? 'flex-end' : 'flex-start',
        maxWidth: '80%',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-xs)',
      }}
    >
      <SkeletonBlock width={60} height={12} />
      <div
        style={{
          padding: 'var(--spacing-sm) var(--spacing-md)',
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: isUser ? '#f2e4d2' : 'var(--color-canvas)',
          minWidth: 200,
        }}
      >
        <Text lines={isUser ? 2 : 4} />
      </div>
    </div>
  )
}

/* ─── Chat Skeleton ─── */
function Chat({ count = 4 }: { count?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)', padding: 'var(--spacing-md)' }}>
      {Array.from({ length: count }).map((_, i) => (
        <ChatBubble key={i} isUser={i % 2 === 0} />
      ))}
    </div>
  )
}

/* ─── Home Page Skeleton ─── */
function Home() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-canvas)' }}>
      {/* Hero skeleton */}
      <section style={{ padding: 'var(--spacing-section) var(--spacing-xl)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-xxl)', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            <SkeletonBlock width={140} height={26} style={{ borderRadius: 'var(--rounded-pill)' }} />
            <SkeletonBlock width="70%" height={64} />
            <SkeletonBlock width="50%" height={32} />
            <SkeletonBlock width={48} height={3} style={{ borderRadius: 'var(--rounded-pill)' }} />
            <SkeletonBlock width="90%" height={16} />
            <div style={{ display: 'flex', gap: 'var(--spacing-md)', marginTop: 'var(--spacing-sm)' }}>
              <SkeletonBlock width={120} height={44} style={{ borderRadius: 'var(--rounded-md)' }} />
              <SkeletonBlock width={120} height={44} style={{ borderRadius: 'var(--rounded-md)' }} />
            </div>
          </div>
          <SkeletonBlock height={320} style={{ borderRadius: 'var(--rounded-xl)' }} />
        </div>
      </section>

      {/* Blog section skeleton */}
      <section style={{ padding: 'var(--spacing-section) var(--spacing-xl)', backgroundColor: 'var(--color-surface-soft)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ marginBottom: 'var(--spacing-xl)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
              <SkeletonBlock width={80} height={24} style={{ borderRadius: 'var(--rounded-pill)' }} />
              <SkeletonBlock width={200} height={36} />
              <SkeletonBlock width={320} height={16} />
            </div>
            <SkeletonBlock width={100} height={40} style={{ borderRadius: 'var(--rounded-md)' }} />
          </div>
          <CardGrid count={6} />
        </div>
      </section>
    </div>
  )
}

/* ─── Export Compound Component ─── */
export const Skeleton = {
  Block: SkeletonBlock,
  Card,
  CardGrid,
  ListItem,
  List,
  Text,
  Avatar,
  ChatBubble,
  Chat,
  Home,
}

export default Skeleton
