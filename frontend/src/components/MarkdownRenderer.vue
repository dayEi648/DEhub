<template>
  <div class="markdown-body" v-html="renderedContent" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

interface Props {
  content: string
}
const props = defineProps<Props>()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  highlight: (str: string, lang: string) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch {
        // fallthrough
      }
    }
    return hljs.highlightAuto(str).value
  }
})

const renderedContent = computed(() => {
  return md.render(props.content || '')
})
</script>

<style>
.markdown-body {
  font-family: var(--font-body);
  font-size: 17px;
  line-height: 1.74;
  color: var(--text-primary);
}
.markdown-body p {
  margin-bottom: 24px;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  font-family: var(--font-display);
  font-weight: 600;
  margin-top: 32px;
  margin-bottom: 16px;
}
.markdown-body h1 { font-size: 32px; }
.markdown-body h2 { font-size: 24px; }
.markdown-body h3 { font-size: 20px; }
.markdown-body pre {
  background: var(--text-primary);
  color: var(--text-white);
  padding: 16px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin-bottom: 24px;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}
.markdown-body code {
  background: var(--bg-gray);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
}
.markdown-body blockquote {
  border-left: 4px solid var(--apple-blue);
  padding-left: 16px;
  margin-bottom: 24px;
  color: var(--text-tertiary);
}
.markdown-body ul,
.markdown-body ol {
  padding-left: 24px;
  margin-bottom: 24px;
}
.markdown-body li {
  margin-bottom: 8px;
}
.markdown-body a {
  color: var(--link-blue);
}
.markdown-body a:hover {
  text-decoration: underline;
}
.markdown-body img {
  max-width: 100%;
  border-radius: var(--radius-md);
  margin-bottom: 24px;
}
</style>
