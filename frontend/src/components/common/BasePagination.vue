<template>
  <div class="base-pagination">
    <!-- Total info -->
    <div
      v-if="showTotal"
      class="pagination-total"
    >
      <span>Total: <strong>{{ total }}</strong> items</span>
      <span
        v-if="showRange"
        class="pagination-range"
      >
        ({{ rangeStart }}-{{ rangeEnd }})
      </span>
    </div>

    <!-- Pagination component -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="pageSizes"
      :total="total"
      :layout="layout"
      :background="background"
      :small="small"
      :hide-on-single-page="hideOnSinglePage"
      :prev-text="prevText"
      :next-text="nextText"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <!-- Page jumper -->
    <div
      v-if="showJumper"
      class="pagination-jumper"
    >
      <span>Go to</span>
      <el-input-number
        v-model="jumpPage"
        :min="1"
        :max="maxPage"
        :controls="false"
        size="small"
        style="width: 60px"
        @change="handleJump"
      />
      <span>page</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  total: number
  page?: number
  pageSize?: number
  pageSizes?: number[]
  layout?: string
  background?: boolean
  small?: boolean
  hideOnSinglePage?: boolean
  prevText?: string
  nextText?: string
  showTotal?: boolean
  showRange?: boolean
  showJumper?: boolean
}

interface Emits {
  (e: 'update:page', page: number): void
  (e: 'update:pageSize', pageSize: number): void
  (e: 'change', page: number, pageSize: number): void
  (e: 'size-change', pageSize: number): void
  (e: 'current-change', page: number): void
}

const props = withDefaults(defineProps<Props>(), {
  page: 1,
  pageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  layout: 'total, sizes, prev, pager, next, jumper',
  background: true,
  small: false,
  hideOnSinglePage: false,
  showTotal: true,
  showRange: true,
  showJumper: false
})

const emit = defineEmits<Emits>()

const currentPage = ref(props.page)
const pageSize = ref(props.pageSize)
const jumpPage = ref(props.page)

// Calculate max page
const maxPage = computed(() => Math.ceil(props.total / pageSize.value) || 1)

// Calculate current range
const rangeStart = computed(() => {
  if (props.total === 0) return 0
  return (currentPage.value - 1) * pageSize.value + 1
})

const rangeEnd = computed(() => {
  const end = currentPage.value * pageSize.value
  return Math.min(end, props.total)
})

// Handle page size change
const handleSizeChange = (newPageSize: number) => {
  // Adjust current page if needed
  const newMaxPage = Math.ceil(props.total / newPageSize)
  if (currentPage.value > newMaxPage) {
    currentPage.value = newMaxPage
  }
  emit('update:pageSize', newPageSize)
  emit('update:page', currentPage.value)
  emit('size-change', newPageSize)
  emit('change', currentPage.value, newPageSize)
}

// Handle current page change
const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  emit('update:page', newPage)
  emit('current-change', newPage)
  emit('change', newPage, pageSize.value)
}

// Handle page jump
const handleJump = (value: number) => {
  const validPage = Math.max(1, Math.min(value, maxPage.value))
  currentPage.value = validPage
  emit('update:page', validPage)
  emit('current-change', validPage)
  emit('change', validPage, pageSize.value)
}

// Watch prop changes
watch(() => props.page, (newPage) => {
  currentPage.value = newPage
  jumpPage.value = newPage
})

watch(() => props.pageSize, (newPageSize) => {
  pageSize.value = newPageSize
})

// Sync jumpPage with currentPage
watch(currentPage, (newPage) => {
  jumpPage.value = newPage
})
</script>

<style scoped>
.base-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  gap: 16px;
  flex-wrap: wrap;
}

.pagination-total {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.pagination-total strong {
  color: var(--el-color-primary);
  font-weight: 600;
}

.pagination-range {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
}

.pagination-jumper {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.pagination-jumper :deep(.el-input-number) {
  vertical-align: middle;
}

@media (max-width: 768px) {
  .base-pagination {
    flex-direction: column;
    align-items: center;
  }

  .pagination-total,
  .pagination-jumper {
    width: 100%;
    text-align: center;
  }
}
</style>
