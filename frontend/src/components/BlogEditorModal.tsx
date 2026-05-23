import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { X, Plus, Trash2, Sparkles } from 'lucide-react'
import { validateImageFile, createImagePreview } from '../utils/upload'
import { uploadImage } from '../api/upload'
import { generateBlogSummary } from '../api/blog'
import type { BlogCategoryWithPostCount, BlogPostListItem } from '../types/blog'

interface BlogPostEditItem extends BlogPostListItem {
  content_md?: string
}

interface BlogEditorModalProps {
  post: BlogPostEditItem | null
  categories: BlogCategoryWithPostCount[]
  onClose: () => void
  onSubmit: (data: {
    title: string
    slug: string
    summary: string
    content_md: string
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
  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [coverPreview, setCoverPreview] = useState<string | null>(null)
  const [categoryId, setCategoryId] = useState<number>(categories[0]?.id ?? 0)
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [status, setStatus] = useState<'draft' | 'published'>('draft')
  const [generatingSummary, setGeneratingSummary] = useState(false)

  useEffect(() => {
    if (post) {
      setTitle(post.title)
      setSlug(post.slug)
      setSummary(post.summary || '')
      setContentMd((post as unknown as { content_md?: string }).content_md || '')
      setCoverFile(null)
      setCoverPreview(post.cover_image_url || null)
      setCategoryId(post.category_id)
      setTags(post.tags || [])
      setStatus(post.status as 'draft' | 'published')
    } else {
      setTitle('')
      setSlug('')
      setSummary('')
      setContentMd('')
      setCoverFile(null)
      setCoverPreview(null)
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

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const error = validateImageFile(file)
    if (error) {
      toast.error(error)
      return
    }

    setCoverFile(file)
    try {
      const preview = await createImagePreview(file)
      setCoverPreview(preview)
    } catch {
      // 预览失败不影响主流程
    }
  }

  const handlePaste = async (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData.items
    let imageFile: File | null = null

    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile()
        if (file) {
          imageFile = file
          break
        }
      }
    }

    if (!imageFile) return

    e.preventDefault()
    const error = validateImageFile(imageFile)
    if (error) {
      toast.error(error)
      return
    }

    const textarea = e.currentTarget
    const start = textarea.selectionStart
    const end = textarea.selectionEnd

    toast.promise(
      uploadImage(imageFile, 'generic').then((res) => {
        const imageUrl = res.data.url
        const alt = imageFile!.name.replace(/\.[^/.]+$/, '') || '图片'
        const markdown = `![${alt}](${imageUrl})`
        const newContent = contentMd.slice(0, start) + markdown + contentMd.slice(end)
        setContentMd(newContent)
        // 将光标移到插入内容之后
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd = start + markdown.length
          textarea.focus()
        }, 0)
      }),
      {
        loading: '正在上传图片...',
        success: '图片上传成功',
        error: (err: unknown) => {
          const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message
          return msg || '图片上传失败'
        },
      }
    )
  }

  const handleSubmit = () => {
    if (!title.trim() || !contentMd.trim() || !categoryId) return
    onSubmit({
      title: title.trim(),
      slug: slug.trim(),
      summary: summary.trim(),
      content_md: contentMd.trim(),
      category_id: categoryId,
      tags,
      status,
      file: coverFile ?? undefined,
    })
  }

  const handleGenerateSummary = async () => {
    const content = contentMd.trim()
    if (content.length < 100) {
      toast.error('正文至少 100 字符后才能生成摘要')
      return
    }
    setGeneratingSummary(true)
    try {
      const res = await generateBlogSummary(content)
      setSummary(res.data.summary)
      toast.success('摘要已生成')
    } catch {
      toast.error('摘要生成失败，请稍后重试')
    } finally {
      setGeneratingSummary(false)
    }
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--spacing-sm)' }}>
              <label style={labelStyle}>摘要</label>
              <button
                type="button"
                onClick={handleGenerateSummary}
                disabled={generatingSummary || submitting || contentMd.trim().length < 100}
                style={{
                  height: 30,
                  padding: '0 12px',
                  borderRadius: 'var(--rounded-pill)',
                  border: '1px solid var(--color-hairline)',
                  backgroundColor: 'var(--color-surface-card)',
                  color: 'var(--color-ink)',
                  fontSize: 12,
                  fontWeight: 500,
                  cursor: generatingSummary || submitting || contentMd.trim().length < 100 ? 'not-allowed' : 'pointer',
                  opacity: generatingSummary || submitting || contentMd.trim().length < 100 ? 0.55 : 1,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 'var(--spacing-xs)',
                }}
              >
                <Sparkles size={13} />
                {generatingSummary ? '生成中…' : '轻量 AI 生成'}
              </button>
            </div>
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
            <label style={labelStyle}>封面图片 {!isEdit ? '*' : ''}</label>
            <div style={{ display: 'flex', gap: 'var(--spacing-xs)', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: 'var(--color-muted)', flex: 1 }}>
                {coverFile ? coverFile.name : (isEdit && coverPreview ? '使用现有封面' : '未选择文件')}
              </span>
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
                选择文件
                <input type="file" accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }} onChange={handleFileChange} />
              </label>
              {!isEdit && (coverFile || coverPreview) && (
                <button
                  onClick={() => {
                    setCoverFile(null)
                    setCoverPreview(null)
                  }}
                  style={{
                    height: 40,
                    padding: '0 14px',
                    borderRadius: 'var(--rounded-md)',
                    backgroundColor: 'var(--color-canvas)',
                    border: '1px solid var(--color-hairline)',
                    color: 'var(--color-error)',
                    fontSize: 13,
                    cursor: 'pointer',
                  }}
                >
                  清除
                </button>
              )}
            </div>
            {coverPreview && (
              <div style={{ marginTop: 'var(--spacing-xs)' }}>
                <img
                  src={coverPreview}
                  alt="封面预览"
                  style={{
                    maxWidth: '100%',
                    maxHeight: 160,
                    borderRadius: 'var(--rounded-md)',
                    objectFit: 'cover',
                    border: '1px solid var(--color-hairline)',
                  }}
                />
              </div>
            )}
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
              onPaste={handlePaste}
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
            disabled={submitting || !title.trim() || !contentMd.trim() || !categoryId || (!isEdit && !coverFile)}
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
