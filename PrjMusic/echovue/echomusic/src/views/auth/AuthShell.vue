<script setup lang="ts">
import './auth.css'
</script>

<template>
  <div class="auth-shell">
    <div class="auth-shell__glow" aria-hidden="true" />
    <div class="auth-shell__glow auth-shell__glow--2" aria-hidden="true" />
    <div class="auth-waves" aria-hidden="true">
      <span /><span /><span /><span /><span />
    </div>
    <slot />
  </div>
</template>
