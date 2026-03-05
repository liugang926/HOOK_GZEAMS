<template>
  <div class="auth-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Authentication layout - simple container for login/register pages
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f8fafc 0%, $bg-body 55%, #e9eef5 100%);
}
</style>
