import { useState, useEffect } from 'react'
import { X, Plus, Trash2 } from 'lucide-react'
import type { BlogCategoryWithPostCount, BlogPostListItem } from '../types/blog'

interface BlogEditorModalProps {
  post: BlogPostListItem | null
  categories: BlogCategoryWithPostCount[]
  onClose: () => void
  onSubmit: (data: {
    title: string
    slug: string
    summary: string
    content_md: string
    cover_image_url: string
    category_id: number
    tags: string[]
    status: 'draft' | 'published'
    file?: File
  }) => void
  submitting?: boolean
}

export default function BlogEditorModal({
  post,
  categories,
  onClose,
  onSubmit,
  submitting = false,
}: BlogEditorModalProps) {
  const isEdit = !!post
  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [summary, setSummary] = useState('')
  const [contentMd, setContentMd] = useState('')
  const [coverUrl, setCoverUrl] = useState('')
  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [categoryId, setCategoryId] = useState<number>(categories[0]?.id ?? 0)
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [status, setStatus] = useState<'draft' | 'published'>('draft')

  useEffect(() => {
    if (post) {
      setTitle(post.title)
      setSlug(post.slug)
      setSummary(post.summary || '')
      setContentMd('')
      setCoverUrl(post.cover_image_url || '')
      setCoverFile(null)
      setCategoryId(post.category_id)
      setTags(post.tags || [])
      setStatus(post.status as 'draft' | 'published')
    } else {
      setTitle('')
      setSlug('')
      setSummary('')
      setContentMd('')
      setCoverUrl('')
      setCoverFile(null)
      setCategoryId(categories[0]?.id ?? 0)
      setTags([])
      setStatus('draft')
    }
  }, [post, categories])

  const handleAddTag = () => {
    const t = tagInput.trim()
    if (!t) return
    if (!tags.includes(t)) {
      setTags((prev) => [...prev, t])
    }
    setTagInput('')
  }

  const handleRemoveTag = (t: string) => {
    setTags((prev) => prev.filter((x) => x !== t))
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setCoverFile(file)
      setCoverUrl('')
    }
  }

  const handleSubmit = () => {
    if (!title.trim() || !contentMd.trim() || !categoryId) return
    onSubmit({
      title: title.trim(),
      slug: slug.trim(),
      summary: summary.trim(),
      content_md: contentMd.trim(),
      cover_image_url: coverUrl.trim(),
      category_id: categoryId,
      tags,
      status,
      file: coverFile ?? undefined,
    })
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    height: 40,
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
    lineHeight: 1.4,
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
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: 'var(--rounded-lg)',
          width: '100%',
          maxWidth: 720,
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(20,20,19,0.15)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: 'var(--spacing-lg) var(--spacing-xl)',
            borderBottom: '1px solid var(--color-hairline)',
          }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 500, margin: 0, color: 'var(--color-ink)' }}>
            {isEdit ? '编辑文章' : '新建文章'}
          </h2>
          <button
            onClick={onClose}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-full)',
              backgroundColor: 'var(--color-surface-card)',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-muted)',
              cursor: 'pointer',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div
          style={{
            padding: 'var(--spacing-xl)',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-md)',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
            <div>
              <label style={labelStyle}>标题 *</label>
              <input type="text" placeholder="文章标题" style={inputStyle} value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Slug</label>
              <input type="text" placeholder="URL 标识（留空自动生成）" style={inputStyle} value={slug} onChange={(e) => setSlug(e.target.value)} />
            </div>
          </div>

          <div>
            <label style={labelStyle}>摘要</label>
            <input type="text" placeholder="文章摘要" style={inputStyle} value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
            <div>
              <label style={labelStyle}>分类 *</label>
              <select
                style={inputStyle}
                value={categoryId}
                onChange={(e) => setCategoryId(Number(e.target.value))}
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={labelStyle}>状态</label>
              <select
                style={inputStyle}
                value={status}
                onChange={(e) => setStatus(e.target.value as 'draft' | 'published')}
              >
                <option value="draft">草稿</option>
                <option value="published">已发布</option>
              </select>
            </div>
          </div>

          <div>
            <label style={labelStyle}>标签</label>
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)', marginBottom: 8 }}>
              {tags.map((t) => (
                <span
                  key={t}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 4,
                    padding: '4px 10px',
                    borderRadius: 'var(--rounded-pill)',
                    backgroundColor: 'var(--color-surface-card)',
                    fontSize: 12,
                    color: 'var(--color-muted)',
                  }}
                >
                  {t}
                  <button
                    onClick={() => handleRemoveTag(t)}
                    style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', color: 'var(--color-muted)', display: 'flex' }}
                  >
                    <Trash2 size={10} />
                  </button>
                </span>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
              <input
                type="text"
                placeholder="输入标签后回车添加"
                style={{ ...inputStyle, flex: 1 }}
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleAddTag()
                  }
                }}
              />
              <button
                onClick={handleAddTag}
                style={{
                  height: 40,
                  padding: '0 14px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-surface-card)',
                  border: '1px solid var(--color-hairline)',
                  color: 'var(--color-ink)',
                  fontSize: 13,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <Plus size={14} />
                添加
              </button>
            </div>
          </div>

          <div>
            <label style={labelStyle}>封面图片</label>
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="封面图 URL（或上传文件）"
                style={{ ...inputStyle, flex: 1 }}
                value={coverUrl}
                onChange={(e) => {
                  setCoverUrl(e.target.value)
                  setCoverFile(null)
                }}
              />
              <label
                style={{
                  height: 40,
                  padding: '0 14px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'var(--color-surface-card)',
                  border: '1px solid var(--color-hairline)',
                  color: 'var(--color-ink)',
                  fontSize: 13,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  whiteSpace: 'nowrap',
                }}
              >
                <Plus size={14} />
                {coverFile ? coverFile.name : '上传文件'}
                <input type="file" accept="image/*" style={{ display: 'none' }} onChange={handleFileChange} />
              </label>
            </div>
          </div>

          <div>
            <label style={labelStyle}>正文 (Markdown) *</label>
            <textarea
              placeholder="支持 Markdown 格式"
              style={{
                ...inputStyle,
                height: 240,
                resize: 'vertical',
                fontFamily: 'var(--font-body)',
              }}
              value={contentMd}
              onChange={(e) => setContentMd(e.target.value)}
            />
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 'var(--spacing-sm)',
            padding: 'var(--spacing-md) var(--spacing-xl)',
            borderTop: '1px solid var(--color-hairline)',
          }}
        >
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
            disabled={submitting || !title.trim() || !contentMd.trim() || !categoryId}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: submitting ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: submitting || !title.trim() || !contentMd.trim() || !categoryId ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? '保存中…' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  fontWeight: 500,
  color: 'var(--color-muted)',
  marginBottom: 'var(--spacing-xs)',
  textTransform: 'uppercase',
  letterSpacing: '1px',
}
