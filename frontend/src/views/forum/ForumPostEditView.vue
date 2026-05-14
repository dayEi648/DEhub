<template>
  <div class="forum-edit-page">
    <div class="container">
      <h1 class="page-title">{{ isEdit ? '编辑帖子' : '发表帖子' }}</h1>
      <div class="editor-form">
        <div class="form-group">
          <label>标题</label>
          <input v-model="form.title" class="form-input" placeholder="帖子标题（1-128 字符）" />
          <p v-if="errors.title" class="error-text">{{ errors.title }}</p>
        </div>
        <div class="form-group">
          <label>分区</label>
          <select v-model="form.zone_id" class="form-input">
            <option disabled :value="undefined">请选择分区</option>
            <option v-for="zone in forumStore.zones" :key="zone.id" :value="zone.id">{{ zone.zone_name }}</option>
          </select>
          <p v-if="errors.zone_id" class="error-text">{{ errors.zone_id }}</p>
        </div>
        <div class="form-group">
          <label>内容</label>
          <textarea
            v-model="form.content"
            class="form-input editor-textarea"
            rows="15"
            placeholder="在此输入内容..."
          />
          <p v-if="errors.content" class="error-text">{{ errors.content }}</p>
        </div>
        <div class="form-actions">
          <PrimaryButton @click="handleSubmit">发布</PrimaryButton>
          <PillLink @click="$router.back()">取消</PillLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { useForumStore } from '@/stores/forum'
import PrimaryButton from '@/components/PrimaryButton.vue'
import PillLink from '@/components/PillLink.vue'

const route = useRoute()
const router = useRouter()
const forumStore = useForumStore()

const isEdit = computed(() => route.name === 'forum-post-edit')
const errors = reactive<Record<string, string>>({})

const form = reactive({
  title: '',
  content: '',
  zone_id: undefined as number | undefined
})

onMounted(async () => {
  await initForm()
})

onBeforeRouteUpdate(async (to) => {
  if (to.name === 'forum-post-edit' && to.params.postId !== route.params.postId) {
    await initForm(Number(to.params.postId))
  }
})

async function initForm(editPostId?: number) {
  if (forumStore.zones.length === 0) {
    await forumStore.fetchZones()
  }
  if (isEdit.value) {
    const postId = editPostId || Number(route.params.postId)
    await forumStore.fetchPostById(postId)
    const post = forumStore.currentPost
    if (post) {
      form.title = post.title
      form.content = post.content
      form.zone_id = post.zone_id
    }
  } else {
    form.title = ''
    form.content = ''
    const zoneId = route.query.zoneId
    form.zone_id = zoneId ? Number(zoneId) : undefined
  }
}

function validate(): boolean {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (!form.title || form.title.length < 1 || form.title.length > 128) {
    errors.title = '标题必填，1-128 字符'
  }
  if (!form.content) {
    errors.content = '内容必填'
  }
  if (!form.zone_id) {
    errors.zone_id = '请选择分区'
  }
  return Object.keys(errors).length === 0
}

async function handleSubmit() {
  if (!validate()) return
  try {
    if (isEdit.value && forumStore.currentPost) {
      await forumStore.updatePost(forumStore.currentPost.id, { ...form })
      router.push(`/forum/post/${forumStore.currentPost.id}`)
    } else {
      const post = await forumStore.createPost({ ...form } as any)
      router.push(`/forum/post/${post.id}`)
    }
  } catch (err: any) {
    errors.submit = err.response?.data?.message || '提交失败'
  }
}
</script>

<style scoped>
.forum-edit-page {
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
.editor-form {
  max-width: 720px;
  margin: 0 auto;
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
.form-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
}
</style>
