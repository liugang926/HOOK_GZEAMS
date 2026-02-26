<template>
  <el-config-provider :locale="elementLocale">
    <div id="app">
      <router-view />
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
/**
 * GZEAMS Root Component
 *
 * Main application entry point with router-view.
 * Provides Element Plus locale configuration reactively.
 */
import { computed } from 'vue'
import { ElConfigProvider } from 'element-plus'
import { useLocaleStore } from '@/stores/locale'

const localeStore = useLocaleStore()
const elementLocale = computed(() => localeStore.elementLocale)
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
}
</style>
