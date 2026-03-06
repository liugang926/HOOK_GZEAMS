<template>
  <el-popover
    v-if="showPopover"
    trigger="hover"
    placement="top-start"
    :width="popoverWidth"
    popper-class="reference-record-pill-popover"
    @show="$emit('show')"
  >
    <template #reference>
      <component
        :is="href ? 'el-link' : 'span'"
        :href="href || undefined"
        :target="href ? '_blank' : undefined"
        type="primary"
        class="reference-record-pill__trigger"
        :underline="false"
      >
        <span class="reference-record-pill__label">{{ label }}</span>
        <span
          v-if="secondary"
          class="reference-record-pill__secondary-inline"
        >
          {{ secondary }}
        </span>
      </component>
    </template>

    <div class="reference-record-pill__card">
      <div class="reference-record-pill__header">
        <ObjectAvatar
          :object-code="objectCode || 'Ref'"
          size="md"
        />
        <div class="reference-record-pill__title-wrap">
          <div class="reference-record-pill__title">
            {{ label }}
          </div>
          <div
            v-if="secondary"
            class="reference-record-pill__subtitle"
          >
            {{ secondary }}
          </div>
        </div>
        <el-tag
          v-if="showObjectTag && objectCode"
          size="small"
          effect="plain"
          type="info"
        >
          {{ objectCode }}
        </el-tag>
      </div>

      <el-divider class="reference-record-pill__divider" />

      <div
        v-if="loading"
        class="reference-record-pill__body is-loading"
      >
        <el-skeleton
          animated
          :rows="3"
        />
      </div>
      <div
        v-else-if="metaItems.length > 0"
        class="reference-record-pill__body"
      >
        <div class="reference-record-pill__meta-grid">
          <div
            v-for="item in metaItems"
            :key="`${item.label}-${item.value}`"
            class="reference-record-pill__meta-item"
          >
            <span class="reference-record-pill__meta-label">{{ item.label }}</span>
            <span class="reference-record-pill__meta-value">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <div class="reference-record-pill__footer">
        <span
          v-if="recordId"
          class="reference-record-pill__id"
        >
          {{ idLabel }}: {{ recordId }}
        </span>
        <el-button
          v-if="href"
          tag="a"
          :href="href"
          target="_blank"
          type="primary"
          size="small"
          plain
        >
          {{ openActionText }}
        </el-button>
      </div>
    </div>
  </el-popover>

  <component
    :is="href ? 'el-link' : 'span'"
    v-else
    :href="href || undefined"
    :target="href ? '_blank' : undefined"
    type="primary"
    class="reference-record-pill__trigger"
    :underline="false"
  >
    <span class="reference-record-pill__label">{{ label }}</span>
    <span
      v-if="secondary"
      class="reference-record-pill__secondary-inline"
    >
      {{ secondary }}
    </span>
  </component>
</template>

<script setup lang="ts">
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'

export interface ReferenceRecordMetaItem {
  label: string
  value: string
}

withDefaults(defineProps<{
  label: string
  secondary?: string
  href?: string
  objectCode?: string
  recordId?: string
  showPopover?: boolean
  showObjectTag?: boolean
  loading?: boolean
  metaItems?: ReferenceRecordMetaItem[]
  popoverWidth?: number
  idLabel?: string
  openActionText?: string
}>(), {
  secondary: '',
  href: '',
  objectCode: '',
  recordId: '',
  showPopover: true,
  showObjectTag: true,
  loading: false,
  metaItems: () => [],
  popoverWidth: 360,
  idLabel: 'ID',
  openActionText: 'Open'
})

defineEmits<{
  (e: 'show'): void
}>()
</script>

<style scoped lang="scss">
.reference-record-pill__trigger {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
  max-width: 100%;
}

.reference-record-pill__label {
  color: var(--el-color-primary);
  font-size: 14px;
  line-height: 1.35;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-record-pill__secondary-inline {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-record-pill__card {
  display: flex;
  flex-direction: column;
}

.reference-record-pill__header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.reference-record-pill__title-wrap {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.reference-record-pill__title {
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.35;
}

.reference-record-pill__subtitle {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.3;
}

.reference-record-pill__divider {
  margin: 10px 0 !important;
}

.reference-record-pill__body {
  padding-bottom: 8px;
}

.reference-record-pill__body.is-loading {
  padding-top: 2px;
}

.reference-record-pill__meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
}

.reference-record-pill__meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.reference-record-pill__meta-label {
  color: var(--el-text-color-secondary);
  font-size: 11px;
}

.reference-record-pill__meta-value {
  color: var(--el-text-color-regular);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reference-record-pill__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.reference-record-pill__id {
  color: var(--el-text-color-secondary);
  font-size: 11px;
  font-family: 'Consolas', 'Monaco', monospace;
}
</style>
