<template>
  <div class="blog-edit-page">
    <div class="editor-container">
      <h1 class="page-title">{{ isEdit ? '编辑文章' : '撰写文章' }}</h1>
      <div class="editor-layout">
        <div class="editor-form">
          <div class="form-group">
            <label>标题</label>
            <input v-model="form.title" class="form-input" placeholder="文章标题" />
            <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
          </div>
          <div class="form-group">
            <div class="summary-header">
              <label>摘要</label>
              <button
                type="button"
                class="ai-generate-btn"
                :disabled="generatingSummary || form.content_md.length < 100"
                @click="handleGenerateSummary"
              >
                {{ generatingSummary ? '生成中…' : '🪄 AI 生成摘要' }}
              </button>
            </div>
            <textarea v-model="form.summary" class="form-input" rows="3" placeholder="文章摘要，可手动填写或点击 AI 生成" />
            <p v-if="form.content_md.length < 100" class="hint-text">正文至少 100 字才可使用 AI 生成摘要</p>
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="form.category_id" class="form-input">
              <option v-for="cat in blogStore.categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
            <p v-if="blogStore.categories.length === 0" class="error-text">请先创建分类</p>
            <p v-else-if="errors.category_id" class="error-text">{{ errors.category_id }}</p>
          </div>
          <div class="form-group">
            <label>标签</label>
            <TagInput v-model="form.tags" />
          </div>
          <div class="form-group">
            <label>封面图</label>
            <div class="cover-uploader" @click="triggerCoverInput">
              <img v-if="coverPreview || form.cover_image_url" :src="coverPreview || form.cover_image_url" class="cover-preview" />
              <div v-else class="cover-placeholder">
                <span class="upload-icon">📷</span>
                <span>点击上传封面图</span>
              </div>
              <div class="upload-overlay">
                <span>更换图片</span>
              </div>
              <input
                ref="coverInput"
                type="file"
                accept="image/*"
                hidden
                @change="handleCoverChange"
              />
            </div>
          </div>
          <div class="form-group">
            <label>正文 (Markdown)</label>
            <textarea
              v-model="form.content_md"
              class="form-input editor-textarea"
              rows="30"
              placeholder="在此输入 Markdown 内容..."
              @keydown.tab.prevent="insertTab"
            />
            <p v-if="errors.content_md" class="error-text">{{ errors.content_md }}</p>
          </div>
          <div v-if="authStore.isSuperAdmin" class="form-group">
            <label>状态</label>
            <div class="segmented-control">
              <button
                class="segment"
                :class="{ active: form.status === 'draft' }"
                @click="form.status = 'draft'"
              >
                草稿
              </button>
              <button
                class="segment"
                :class="{ active: form.status === 'published' }"
                @click="form.status = 'published'"
              >
                已发布
              </button>
            </div>
          </div>
          <div class="form-actions">
            <PrimaryButton @click="handleSave">保存</PrimaryButton>
            <PillLink @click="$router.back()">取消</PillLink>
          </div>
        </div>
        <div class="editor-preview">
          <Card class="preview-card">
            <div class="preview-header">实时预览</div>
            <MarkdownRenderer :content="form.content_md" />
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, onUnmounted, computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blog'
import { useUiStore } from '@/stores/ui'
import { compressImage } from '@/utils/imageCompress'
import { generateSummary } from '@/api/blog'
import PrimaryButton from '@/components/PrimaryButton.vue'
import PillLink from '@/components/PillLink.vue'
import Card from '@/components/Card.vue'
import TagInput from '@/components/TagInput.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const blogStore = useBlogStore()

const isEdit = computed(() => route.name === 'blog-edit')
const errors = reactive<Record<string, string>>({})
const form = reactive({
  title: '',
  summary: '',
  content_md: '',
  cover_image_url: '',
  category_id: undefined as number | undefined,
  tags: [] as string[],
  status: 'draft' as 'draft' | 'published'
})

const uiStore = useUiStore()
const coverInput = ref<HTMLInputElement>()
const coverPreview = ref<string | null>(null)
const selectedCoverFile = ref<File | null>(null)
const generatingSummary = ref(false)

function triggerCoverInput() {
  coverInput.value?.click()
}

async function handleCoverChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 10 * 1024 * 1024) {
    uiStore.showToast('文件大小不能超过 10MB', 'error')
    return
  }

  uiStore.showToast('正在压缩图片…')
  try {
    const compressed = await compressImage(file, 1920, 1080, 5 * 1024 * 1024)
    selectedCoverFile.value = compressed
    if (coverPreview.value) {
      URL.revokeObjectURL(coverPreview.value)
    }
    coverPreview.value = URL.createObjectURL(compressed)
    uiStore.showToast('图片压缩完成', 'success')
  } catch (err: any) {
    uiStore.showToast(err.message || '图片压缩失败', 'error')
  }
}

onUnmounted(() => {
  if (coverPreview.value) {
    URL.revokeObjectURL(coverPreview.value)
  }
})

onMounted(() => {
  blogStore.fetchCategories()
  if (isEdit.value) {
    const slug = route.params.slug as string
    blogStore.fetchPostBySlug(slug).then(() => {
      const post = blogStore.currentPost
      if (post) {
        form.title = post.title
        form.summary = post.summary || ''
        form.content_md = post.content_md
        form.cover_image_url = post.cover_image_url || ''
        form.category_id = post.category_id
        form.tags = [...post.tags]
        form.status = post.status as 'draft' | 'published'
      }
    })
  }
})

function insertTab(e: KeyboardEvent) {
  const target = e.target as HTMLTextAreaElement
  const start = target.selectionStart
  const end = target.selectionEnd
  form.content_md = form.content_md.substring(0, start) + '  ' + form.content_md.substring(end)
  setTimeout(() => {
    target.selectionStart = target.selectionEnd = start + 2
  })
}

function validate(): boolean {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (!form.title || form.title.length < 1 || form.title.length > 64) {
    errors.title = '标题必填，1-64 字符'
  }
  if (!form.content_md) {
    errors.content_md = '正文必填'
  }
  if (!form.category_id) {
    errors.category_id = '请选择分类'
  }
  return Object.keys(errors).length === 0
}

async function handleGenerateSummary() {
  if (form.content_md.length < 100) {
    uiStore.showToast('正文内容不足，请至少写 100 字后再生成摘要', 'error')
    return
  }
  generatingSummary.value = true
  try {
    const { data } = await generateSummary(form.content_md)
    form.summary = data.summary
    uiStore.showToast('摘要生成成功', 'success')
  } catch (err: any) {
    const message = err.response?.data?.detail || '摘要生成失败，请稍后重试'
    uiStore.showToast(message, 'error')
  } finally {
    generatingSummary.value = false
  }
}

async function handleSave() {
  if (!validate()) return
  const payload = { ...form }
  try {
    if (isEdit.value && blogStore.currentPost) {
      await blogStore.updatePost(blogStore.currentPost.id, payload, selectedCoverFile.value || undefined)
      router.push(`/blog/${blogStore.currentPost.slug}`)
    } else {
      const post = await blogStore.createPost(payload as any, selectedCoverFile.value || undefined)
      router.push(`/blog/${post.slug}`)
    }
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (detail) {
      detail.forEach((d: any) => {
        const field = d.loc?.[d.loc.length - 1]
        if (field) errors[field] = d.msg
      })
    }
  }
}
</script>

<style scoped>
.blog-edit-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 24px 0;
}
.editor-container {
  width: 100%;
  padding-left: 24px;
  padding-right: 24px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 24px;
}
.editor-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 1024px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }
}
.editor-form {
  max-width: none;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
}
.form-input:focus {
  border-color: var(--apple-blue);
}
.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.ai-generate-btn {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--apple-blue);
  background: rgba(0, 113, 227, 0.08);
  border: 1px solid rgba(0, 113, 227, 0.2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.ai-generate-btn:hover:not(:disabled) {
  background: rgba(0, 113, 227, 0.15);
}
.ai-generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.hint-text {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
.editor-textarea {
  font-family: monospace;
  line-height: 1.6;
}
.error-text {
  font-size: 12px;
  color: var(--error-red);
  margin-top: 4px;
}
.segmented-control {
  display: inline-flex;
  background: var(--button-default-light);
  border-radius: var(--radius-md);
  padding: 3px;
}
.segment {
  padding: 6px 16px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.segment.active {
  background: var(--text-white);
  color: var(--text-primary);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.cover-uploader {
  position: relative;
  width: 100%;
  max-width: 400px;
  aspect-ratio: 16 / 10;
  background: var(--button-default-light);
  border: 2px dashed rgba(0, 0, 0, 0.12);
  border-radius: var(--radius-lg);
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cover-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-tertiary);
  font-size: 14px;
}
.upload-icon {
  font-size: 28px;
}
.cover-uploader .upload-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  color: var(--text-white);
  font-size: 14px;
  font-weight: 500;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.cover-uploader:hover .upload-overlay {
  opacity: 1;
}
.form-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}
.editor-preview {
  position: sticky;
  top: 80px;
  align-self: start;
}
.preview-card {
  padding: 24px;
}
.preview-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}
</style>
