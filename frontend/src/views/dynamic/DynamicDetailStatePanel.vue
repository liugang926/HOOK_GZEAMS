<template>
  <div class="load-error">
    <el-result
      :icon="icon"
      :title="title"
      :sub-title="subTitle"
    >
      <template #extra>
        <el-button
          v-if="showRefresh"
          type="primary"
          @click="emit('refresh')"
        >
          {{ refreshLabel }}
        </el-button>
        <el-button @click="emit('back')">
          {{ backLabel }}
        </el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon: 'error' | 'warning' | 'success' | 'info'
  title: string
  subTitle: string
  backLabel: string
  refreshLabel?: string
  showRefresh?: boolean
}

withDefaults(defineProps<Props>(), {
  refreshLabel: '',
  showRefresh: false,
})

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'refresh'): void
}>()
</script>
