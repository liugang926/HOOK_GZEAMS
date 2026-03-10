<!--
  RelatedRecordDrawer Component

  Displays a related record's compact details in a right-side drawer
  instead of navigating to a full detail page.

  Features:
  - Loads compact detail fields via API
  - Shows record name/code header with object avatar
  - "View Full Detail" button to navigate to full page
  - Smooth slide-in animation
-->

<template>
  <el-drawer
    :model-value="visible"
    :title="drawerTitle"
    direction="rtl"
    :size="480"
    :destroy-on-close="true"
    class="related-record-drawer"
    @close="handleClose"
  >
    <template #header>
      <div class="drawer-header">
        <ObjectAvatar
          :object-code="objectCode"
          size="md"
        />
        <div class="drawer-header-text">
          <div class="drawer-header-object">
            {{ objectDisplayName }}
          </div>
          <div class="drawer-header-title">
            {{ recordDisplayName || recordId }}
          </div>
        </div>
      </div>
    </template>

    <div
      v-loading="loading"
      class="drawer-body"
    >
      <el-empty
        v-if="!loading && compactFields.length === 0"
        :description="t('common.messages.noData')"
      />

      <div
        v-else
        class="compact-field-list"
      >
        <div
          v-for="field in compactFields"
          :key="field.fieldCode"
          class="compact-field-item"
        >
          <span class="compact-field-label">{{ field.label }}</span>
          <span class="compact-field-value">{{ field.value || '-' }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <el-button
          @click="handleClose"
        >
          {{ t('common.actions.close') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleViewFullDetail"
        >
          {{ t('common.actions.viewDetail', '查看详情') }}
        </el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import { useReferenceCache } from '@/composables/useReferenceCache'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import type { CompactDetailField } from '@/api/dynamic'

const props = withDefaults(defineProps<{
  visible: boolean
  objectCode: string
  recordId: string
  recordDisplayName?: string
}>(), {
  recordDisplayName: ''
})

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'close'): void
  (e: 'navigate', objectCode: string, recordId: string): void
}>()

const { t, te } = useI18n()
const router = useRouter()
const { getCompactDetail } = useReferenceCache()

const loading = ref(false)
const compactFields = ref<CompactDetailField[]>([])

const objectDisplayName = computed(() => {
  if (!props.objectCode) return ''
  return resolveObjectDisplayName(props.objectCode, props.objectCode, t, te)
})

const drawerTitle = computed(() => {
  return objectDisplayName.value || props.objectCode
})

const loadCompactDetail = async () => {
  if (!props.objectCode || !props.recordId) {
    compactFields.value = []
    return
  }

  loading.value = true
  try {
    const fields = await getCompactDetail(props.objectCode, props.recordId)
    compactFields.value = fields
  } catch {
    compactFields.value = []
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

const handleViewFullDetail = () => {
  handleClose()
  router.push(`/objects/${encodeURIComponent(props.objectCode)}/${encodeURIComponent(props.recordId)}`)
}

watch(
  () => [props.visible, props.objectCode, props.recordId] as const,
  ([isVisible]) => {
    if (isVisible && props.objectCode && props.recordId) {
      loadCompactDetail()
    }
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.drawer-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.drawer-header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.drawer-header-object {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.2;
}

.drawer-header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-body {
  min-height: 200px;
}

.compact-field-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.compact-field-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-bottom: none;
  }
}

.compact-field-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
  max-width: 40%;
}

.compact-field-value {
  font-size: 14px;
  color: var(--el-text-color-primary);
  font-weight: 500;
  text-align: right;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
