<template>
  <footer class="global-footer">
    <div class="container">
      <p class="footer-text">DE hub — A personal platform for developers</p>
      <p class="footer-copy">Built with Vue 3, FastAPI & Apple Design</p>
    </div>
  </footer>
</template>

<style scoped>
.global-footer {
  padding: 40px 0;
  background: var(--bg-black);
  text-align: center;
}
.footer-text {
  font-family: var(--font-display);
  font-size: 14px;
  color: var(--text-white);
  margin-bottom: 8px;
}
.footer-copy {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.48);
}
</style>
