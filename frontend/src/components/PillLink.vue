<template>
  <component
    :is="to ? 'router-link' : 'button'"
    :to="to"
    class="pill-link"
    @click="$emit('click', $event)"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
interface Props {
  to?: string
}
defineProps<Props>()
defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<style scoped>
.pill-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.43;
  letter-spacing: -0.224px;
  color: var(--link-blue);
  background-color: transparent;
  border: 1px solid var(--link-blue);
  border-radius: var(--radius-pill);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}
.pill-link:hover {
  text-decoration: underline;
}
</style>
