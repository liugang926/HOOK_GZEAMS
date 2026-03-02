<template>
  <template v-if="displayType === 'image'">
    <el-image
      v-if="imageList.length > 0"
      :src="imageList[0]"
      fit="cover"
      :preview-src-list="imageList"
      class="detail-image"
    >
      <template #error>
        <div class="image-error">
          <el-icon><Picture /></el-icon>
        </div>
      </template>
    </el-image>
    <span v-else>-</span>
  </template>

  <template v-else-if="displayType === 'link'">
    <el-link
      v-if="linkHref"
      :href="linkHref"
      target="_blank"
      type="primary"
    >
      {{ displayText }}
    </el-link>
    <span v-else>{{ displayText }}</span>
  </template>

  <template v-else-if="displayType === 'tag'">
    <el-tag :type="tagType">
      {{ displayText }}
    </el-tag>
  </template>

  <template v-else>
    <span>{{ displayText }}</span>
  </template>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Picture } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import { formatMoney } from '@/utils/numberFormat'
import { normalizeFieldType } from '@/utils/fieldType'

interface FieldLike {
  type?: string
  fieldType?: string
  dateFormat?: string
  precision?: number
  currency?: string
  options?: { label: string; value: any; color?: string }[]
  tagType?: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  href?: string
}

const props = defineProps<{
  field: FieldLike
  value: any
}>()

const displayType = computed(() => normalizeFieldType(props.field?.fieldType || props.field?.type || 'text'))

const hasValue = computed(() => props.value !== undefined && props.value !== null && props.value !== '')

const safeText = (value: any): string => {
  if (value === undefined || value === null) return '-'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.map(item => safeText(item)).filter(Boolean).join(', ')
  }
  if (typeof value === 'object') {
    return (
      value.name ||
      value.label ||
      value.title ||
      value.code ||
      value.id ||
      value.fileName ||
      value.filename ||
      value.path ||
      value.url ||
      '-'
    )
  }
  return String(value)
}

const resolveOptionLabel = (value: any): string | null => {
  const options = props.field.options || []
  if (!options.length) return null

  const toLabel = (val: any): string | null => {
    const opt = options.find(item => item.value === val)
    return opt ? opt.label : null
  }

  if (Array.isArray(value)) {
    const labels = value.map(toLabel).filter((label): label is string => !!label)
    return labels.length ? labels.join(', ') : null
  }

  return toLabel(value)
}

const displayText = computed(() => {
  if (!hasValue.value) return '-'

  const value = props.value
  const optionLabel = resolveOptionLabel(value)
  switch (displayType.value) {
    case 'date':
      return formatDate(value, props.field.dateFormat || 'YYYY-MM-DD')
    case 'datetime':
      return formatDate(value, props.field.dateFormat || 'YYYY-MM-DD HH:mm:ss')
    case 'time':
      return formatDate(value, props.field.dateFormat || 'HH:mm:ss')
    case 'number':
      if (props.field.precision !== undefined) {
        const num = Number(value)
        return Number.isNaN(num) ? safeText(value) : num.toFixed(props.field.precision)
      }
      return safeText(value)
    case 'currency': {
      const num = Number(value)
      if (Number.isNaN(num)) return safeText(value)
      const formatted = formatMoney(num, props.field.precision ?? 2)
      return `${props.field.currency || '¥'}${formatted}`
    }
    case 'percent': {
      const num = Number(value)
      if (Number.isNaN(num)) return safeText(value)
      return `${num.toFixed(props.field.precision ?? 2)}%`
    }
    default:
      return optionLabel ?? safeText(value)
  }
})

const tagType = computed(() => {
  const raw = props.value
  const options = props.field.options || []
  const option = options.find(item => item.value === raw)
  return props.field.tagType?.[raw] || option?.color || props.field.defaultTagType || 'info'
})

const linkHref = computed(() => {
  if (displayType.value !== 'link' || !props.field.href || !hasValue.value) return ''
  return props.field.href.replace('{value}', String(props.value))
})

const normalizeImageSrc = (item: any): string => {
  if (!item) return ''
  if (typeof item === 'string') return item
  if (typeof item === 'object') {
    return item.url || item.path || item.src || ''
  }
  return String(item)
}

const imageList = computed(() => {
  if (!hasValue.value) return []
  const raw = Array.isArray(props.value) ? props.value : [props.value]
  return raw.map(normalizeImageSrc).filter(Boolean)
})
</script>

<style scoped>
.detail-image {
  width: 120px;
  height: 120px;
  border-radius: 4px;
  overflow: hidden;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: #f5f7fa;
  color: #c0c4cc;
  font-size: 32px;
}
</style>
