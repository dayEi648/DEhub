import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Plus, Trash2 } from 'lucide-react'
import BaseModal from './BaseModal'
import { validateImageFile, createImagePreview } from '../utils/upload'
import { usePasteImageUpload } from '../hooks/usePasteImageUpload'
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
    content_md: string
    category_id: number
    tags: string[]
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
  const [contentMd, setContentMd] = useState('')
  const [coverFile, setCoverFile] = useState<File | null>(null)
  const [coverPreview, setCoverPreview] = useState<string | null>(null)
  const [categoryId, setCategoryId] = useState<number>(categories[0]?.id ?? 0)
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState<string[]>([])

  useEffect(() => {
    if (post) {
      setTitle(post.title)
      setSlug(post.slug)
      setContentMd(post.content_md || '')
      setCoverFile(null)
      setCoverPreview(post.cover_image_url || null)
      setCategoryId(post.category_id)
      setTags(post.tags || [])
    } else {
      setTitle('')
      setSlug('')
      setContentMd('')
      setCoverFile(null)
      setCoverPreview(null)
      setCategoryId(categories[0]?.id ?? 0)
      setTags([])
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

  const { handlePaste } = usePasteImageUpload('generic')

  const isDirty = isEdit
    ? title.trim() !== (post?.title || '') ||
      slug.trim() !== (post?.slug || '') ||
      contentMd.trim() !== (post?.content_md || '') ||
      categoryId !== (post?.category_id ?? 0) ||
      JSON.stringify([...tags].sort()) !== JSON.stringify([...(post?.tags || [])].sort()) ||
      coverFile !== null
    : true

  const handleSubmit = () => {
    if (!title.trim()) {
      toast.error('请输入标题')
      return
    }
    if (!contentMd.trim()) {
      toast.error('请输入正文')
      return
    }
    if (!categoryId) {
      toast.error('请选择分类')
      return
    }
    if (!isEdit && !coverFile) {
      toast.error('请上传封面图片')
      return
    }
    onSubmit({
      title: title.trim(),
      slug: slug.trim(),
      content_md: contentMd.trim(),
      category_id: categoryId,
      tags,
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
    <BaseModal
      title={<h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 500, margin: 0 }}>{isEdit ? '编辑文章' : '新建文章'}</h2>}
      onClose={onClose}
      maxWidth={720}
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
            disabled={submitting || !isDirty || !title.trim() || !contentMd.trim() || !categoryId || (!isEdit && !coverFile)}
            style={{
              height: 40,
              padding: '0 20px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: submitting || !isDirty ? 'var(--color-primary-disabled)' : 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              fontSize: 14,
              fontWeight: 500,
              border: 'none',
              cursor: submitting || !isDirty || !title.trim() || !contentMd.trim() || !categoryId ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? '保存中…' : '保存'}
          </button>
        </>
      }
    >

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

          <div style={{ display: 'grid', gridTemplateColumns: isEdit ? '1fr 1fr' : '1fr', gap: 'var(--spacing-md)' }}>
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
            {isEdit && (
              <div>
                <label style={labelStyle}>状态</label>
                <div
                  style={{
                    ...inputStyle,
                    display: 'flex',
                    alignItems: 'center',
                    color: 'var(--color-muted)',
                  }}
                >
                  {post?.status === 'published' ? '已发布' : '草稿'}
                </div>
              </div>
            )}
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
              onPaste={(e) =>
                handlePaste(e, (md, s, end) => {
                  const newContent = contentMd.slice(0, s) + md + contentMd.slice(end)
                  setContentMd(newContent)
                })
              }
            />
          </div>
        </div>

    </BaseModal>
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
