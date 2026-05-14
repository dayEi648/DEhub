<template>
  <div class="blog-edit-page">
    <div class="container">
      <h1 class="page-title">{{ isEdit ? '编辑文章' : '撰写文章' }}</h1>
      <div class="editor-layout">
        <div class="editor-form">
          <div class="form-group">
            <label>标题</label>
            <input v-model="form.title" class="form-input" placeholder="文章标题" />
            <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
          </div>
          <div class="form-group">
            <label>Slug</label>
            <input v-model="form.slug" class="form-input" placeholder="url-friendly-slug" @input="slugEdited = true" />
            <p v-if="errors.slug" class="error-text">{{ errors.slug }}</p>
          </div>
          <div class="form-group">
            <label>摘要</label>
            <textarea v-model="form.summary" class="form-input" rows="3" placeholder="文章摘要" />
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
            <label>封面图 URL</label>
            <input v-model="form.cover_image_url" class="form-input" placeholder="https://..." />
          </div>
          <div class="form-group">
            <label>正文 (Markdown)</label>
            <textarea
              v-model="form.content_md"
              class="form-input editor-textarea"
              rows="20"
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
import { reactive, onMounted, computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blog'
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
const slugEdited = ref(false)

const form = reactive({
  title: '',
  slug: '',
  summary: '',
  content_md: '',
  cover_image_url: '',
  category_id: undefined as number | undefined,
  tags: [] as string[],
  status: 'draft' as 'draft' | 'published'
})

watch(() => form.title, (title) => {
  if (!isEdit.value && !slugEdited.value && title) {
    form.slug = title.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9\-]/g, '')
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
        form.slug = post.slug
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
  if (!form.slug || form.slug.length < 1 || form.slug.length > 255) {
    errors.slug = 'Slug 必填，1-255 字符'
  }
  if (!form.content_md) {
    errors.content_md = '正文必填'
  }
  if (!form.category_id) {
    errors.category_id = '请选择分类'
  }
  return Object.keys(errors).length === 0
}

async function handleSave() {
  if (!validate()) return
  const payload = { ...form }
  try {
    if (isEdit.value && blogStore.currentPost) {
      await blogStore.updatePost(blogStore.currentPost.id, payload)
      router.push(`/blog/${form.slug}`)
    } else {
      const post = await blogStore.createPost(payload as any)
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
  padding: 40px 0;
}
.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 32px;
}
.editor-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}
@media (max-width: 1024px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }
}
.editor-form {
  max-width: 600px;
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
