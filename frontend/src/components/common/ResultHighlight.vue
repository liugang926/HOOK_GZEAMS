<template>
  <span
    class="result-highlight"
    v-html="displayHtml"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    highlight?: string | string[] | null
    fallback?: string | number | null
  }>(),
  {
    highlight: null,
    fallback: '',
  }
)

const sanitizeHighlight = (value: string) => {
  const startToken = '__ALLOWED_EM_START__'
  const endToken = '__ALLOWED_EM_END__'

  return String(value)
    .replace(/<em\b[^>]*>/gi, startToken)
    .replace(/<\/em>/gi, endToken)
    .replace(/<[^>]+>/g, '')
    .split(startToken)
    .join('<em>')
    .split(endToken)
    .join('</em>')
}

const displayHtml = computed(() => {
  const source = Array.isArray(props.highlight) ? props.highlight[0] : props.highlight
  if (source && String(source).trim()) {
    return sanitizeHighlight(String(source))
  }
  return String(props.fallback ?? '')
})
</script>

<style scoped lang="scss">
.result-highlight {
  :deep(em) {
    font-style: normal;
    font-weight: 700;
    color: #c2410c;
    background: rgba(251, 191, 36, 0.18);
    border-radius: 4px;
    padding: 0 3px;
  }
}
</style>
