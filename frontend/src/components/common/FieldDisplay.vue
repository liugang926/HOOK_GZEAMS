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

  <template v-else-if="displayType === 'qr_code' || displayType === 'barcode'">
    <el-image
      v-if="hasCodeRenderableValue"
      :src="codeImageUrl"
      :preview-src-list="[codeImageUrl]"
      fit="contain"
      :class="displayType === 'barcode' ? 'barcode-image' : 'qr-code-image'"
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

  <template v-else-if="isReferenceDisplay">
    <div
      v-if="referenceEntries.length > 0"
      class="reference-read-view"
    >
      <ReferenceRecordPill
        v-for="(entry, index) in referenceEntries"
        :key="entry.id || `${entry.label}-${index}`"
        :label="entry.label"
        :secondary="entry.secondary"
        :href="entry.href"
        :object-code="referenceObjectCode"
        :record-id="entry.id"
        :source-data="referenceValueFromInput[entry.id] || referenceValueMap[entry.id] || null"
      />
    </div>
    <span v-else>-</span>
  </template>

  <template v-else-if="displayType === 'tag'">
    <el-tag :type="tagType">
      {{ displayText }}
    </el-tag>
  </template>

  <template v-else-if="displayType === 'boolean' || displayType === 'switch' || displayType === 'checkbox'">
    <el-tag :type="booleanTagType">
      {{ booleanText }}
    </el-tag>
  </template>

  <template v-else-if="displayType === 'color'">
    <div
      v-if="colorText !== '-'"
      class="color-display"
    >
      <span
        class="color-swatch"
        :style="{ backgroundColor: colorText }"
      />
      <span>{{ colorText }}</span>
    </div>
    <span v-else>-</span>
  </template>

  <template v-else-if="displayType === 'rate'">
    <el-rate
      :model-value="rateValue"
      disabled
      show-score
      text-color="#ff9900"
    />
  </template>

  <template v-else-if="displayType === 'file' || displayType === 'attachment'">
    <div
      v-if="fileEntries.length > 0"
      class="file-display"
    >
      <div
        v-for="(file, index) in fileEntries"
        :key="`${file.name}-${index}`"
        class="file-item"
      >
        <el-link
          v-if="file.url"
          :href="file.url"
          target="_blank"
          type="primary"
        >
          {{ file.name }}
        </el-link>
        <span v-else>{{ file.name }}</span>
      </div>
    </div>
    <span v-else>-</span>
  </template>

  <template v-else-if="displayType === 'rich_text'">
    <div
      v-if="richTextHtml"
      class="rich-text-display"
      v-html="richTextHtml"
    />
    <span v-else>-</span>
  </template>

  <template v-else-if="displayType === 'sub_table'">
    <div
      v-if="subTableColumns.length > 0 && subTablePreviewRows.length > 0"
      class="subtable-display"
    >
      <el-table
        :data="subTablePreviewRows"
        size="small"
        border
        class="subtable-table"
      >
        <el-table-column
          v-for="column in subTableColumns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          min-width="120"
        >
          <template #default="{ row }">
            {{ formatSubTableCell(row, column.key) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="subtable-meta">
        {{ t('common.table.total', { total: subTableTotalRows }) }}
      </div>
    </div>
    <span v-else>-</span>
  </template>

  <template v-else-if="displayType === 'json' || displayType === 'object'">
    <pre class="json-display">{{ jsonDisplay }}</pre>
  </template>

  <template v-else>
    <span>{{ displayText }}</span>
  </template>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Picture } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import { formatMoney } from '@/utils/numberFormat'
import { normalizeFieldType } from '@/utils/fieldType'
import { systemFileApi, resolveSystemFileUrl, type SystemFile } from '@/api/systemFile'
import ReferenceRecordPill from '@/components/common/ReferenceRecordPill.vue'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import {
  extractReferenceIds,
  isReferenceLikeField,
  isReferenceLikeFieldType,
  resolveReferenceDisplayField,
  resolveReferenceLabel,
  resolveReferenceObjectCode,
  resolveReferenceSecondaryField,
  resolveReferenceSecondaryText
} from '@/platform/reference/referenceFieldMeta'
import {
  buildReferenceValueMap
} from '@/platform/reference/referenceValueAdapter'

interface FieldLike {
  type?: string
  fieldType?: string
  editorType?: string
  dateFormat?: string
  precision?: number
  currency?: string
  size?: number
  width?: number
  height?: number
  referenceObject?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
  options?: { label: string; value: any; color?: string }[]
  tagType?: Record<string, string> | ((value: any, row?: any) => string)
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary' | string
  href?: string
  componentProps?: Record<string, any>
}

interface FileEntry {
  name: string
  url: string
}

interface SubTableColumn {
  key: string
  label: string
}

const props = defineProps<{
  field: FieldLike
  value: any
  deferReferenceResolve?: boolean
}>()
const { t } = useI18n()

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const fileMetadataMap = ref<Record<string, SystemFile>>({})
const metadataRequestToken = ref(0)
const referenceValueMap = ref<Record<string, any>>({})
const referenceRequestToken = ref(0)

const displayType = computed(() =>
  normalizeFieldType(props.field?.editorType || props.field?.fieldType || props.field?.type || 'text')
)

const hasValue = computed(() => props.value !== undefined && props.value !== null && props.value !== '')

const isReferenceDisplay = computed(() => {
  if (isReferenceLikeFieldType(displayType.value)) return true
  return isReferenceLikeField({
    ...(props.field || {}),
    fieldType: props.field?.fieldType || props.field?.type || displayType.value,
    editorType: props.field?.editorType || displayType.value
  })
})

const referenceObjectCode = computed(() => {
  return resolveReferenceObjectCode({
    ...(props.field || {}),
    fieldType: displayType.value
  })
})

const referenceDisplayField = computed(() => {
  return resolveReferenceDisplayField(props.field || {}, 'name')
})

const referenceSecondaryField = computed(() => {
  return resolveReferenceSecondaryField(props.field || {}, 'code')
})

const referenceIds = computed(() => {
  return extractReferenceIds(props.value)
})

const referenceValueFromInput = computed<Record<string, any>>(() => buildReferenceValueMap(props.value))

interface ReferenceEntry {
  id: string
  label: string
  secondary: string
  href: string
}

const toReferenceEntry = (id: string, value: any): ReferenceEntry | null => {
  const label = resolveReferenceLabel(value, referenceDisplayField.value) || id
  if (!label) return null
  const secondary = resolveReferenceSecondaryText(
    value,
    referenceSecondaryField.value,
    referenceDisplayField.value
  )
  const href = referenceObjectCode.value && id
    ? `/objects/${referenceObjectCode.value}/${encodeURIComponent(id)}`
    : ''
  return {
    id,
    label,
    secondary,
    href
  }
}

const referenceEntries = computed<ReferenceEntry[]>(() => {
  const ids = referenceIds.value
  if (ids.length > 0) {
    return ids
      .map((id) => {
        const candidate = referenceValueFromInput.value[id] || referenceValueMap.value[id] || { id }
        return toReferenceEntry(id, candidate)
      })
      .filter((item): item is ReferenceEntry => !!item)
  }

  const primitiveLabel = resolveReferenceLabel(props.value, referenceDisplayField.value)
  if (primitiveLabel) {
    const fallback = toReferenceEntry('', {
      [referenceDisplayField.value || 'name']: primitiveLabel
    })
    return fallback ? [fallback] : []
  }

  if (!props.value || typeof props.value !== 'object') return []
  const fallback = toReferenceEntry('', props.value)
  return fallback ? [fallback] : []
})

const isUuidLike = (value: unknown): value is string => {
  if (typeof value !== 'string') return false
  return UUID_PATTERN.test(value.trim())
}

const collectCandidateFileIds = (value: any, bucket: Set<string>) => {
  if (!value) return

  if (Array.isArray(value)) {
    value.forEach((item) => collectCandidateFileIds(item, bucket))
    return
  }

  if (typeof value === 'string') {
    const parsed = parseMaybeJson(value)
    if (parsed !== value) {
      collectCandidateFileIds(parsed, bucket)
      return
    }
    if (isUuidLike(value)) bucket.add(value.trim())
    return
  }

  if (typeof value !== 'object') return

  const objectValue = value as Record<string, any>
  const candidateId = objectValue.id || objectValue.fileId || objectValue.file_id || objectValue.value
  if (isUuidLike(candidateId)) bucket.add(String(candidateId).trim())

  const nested = objectValue.files || objectValue.items || objectValue.list
  if (nested) collectCandidateFileIds(nested, bucket)
}

const getMetadataById = (value: unknown): SystemFile | null => {
  if (!isUuidLike(value)) return null
  return fileMetadataMap.value[String(value).trim()] || null
}

const resolveImageUrlFromValue = (value: any): string => {
  if (!value) return ''
  if (typeof value === 'string') {
    const parsed = parseMaybeJson(value)
    if (parsed !== value) return resolveImageUrlFromValue(parsed)
    if (isUuidLike(value)) {
      const meta = getMetadataById(value)
      return resolveSystemFileUrl(meta?.thumbnailUrl || meta?.url || '')
    }
    return resolveSystemFileUrl(value)
  }
  if (typeof value === 'object') {
    const meta = getMetadataById((value as any).id || (value as any).fileId || (value as any).file_id)
    if (meta) return resolveSystemFileUrl(meta.thumbnailUrl || meta.url || '')
    return resolveSystemFileUrl(String((value as any).url || (value as any).path || (value as any).src || ''))
  }
  return resolveSystemFileUrl(String(value))
}

const resolveFileEntryFromValue = (value: any): FileEntry | null => {
  if (!value) return null

  if (typeof value === 'string') {
    const parsed = parseMaybeJson(value)
    if (parsed !== value) return resolveFileEntryFromValue(parsed)
    if (isUuidLike(value)) {
      const meta = getMetadataById(value)
      if (meta) {
        return {
          name: meta.fileName || value,
          url: resolveSystemFileUrl(meta.url || '')
        }
      }
    }
    const url = /^https?:\/\//i.test(value) || value.startsWith('/') ? value : ''
    const name = url ? decodeURIComponent(url.split('/').filter(Boolean).pop() || url) : value
    return { name: name || 'file', url: resolveSystemFileUrl(url) }
  }

  if (typeof value === 'object') {
    const candidateId = (value as any).id || (value as any).fileId || (value as any).file_id || (value as any).value
    if (isUuidLike(candidateId)) {
      const meta = getMetadataById(candidateId)
      if (meta) {
        return {
          name: meta.fileName || String(candidateId),
          url: resolveSystemFileUrl(meta.url || '')
        }
      }
    }
    const url = resolveSystemFileUrl(String(
      (value as any).url ||
      (value as any).path ||
      (value as any).filePath ||
      (value as any).file_path ||
      (value as any).downloadUrl ||
      (value as any).download_url ||
      ''
    ))
    const name = String(
      (value as any).name ||
      (value as any).fileName ||
      (value as any).filename ||
      (url ? decodeURIComponent(url.split('/').filter(Boolean).pop() || url) : '') ||
      'file'
    )
    if (!name && !url) return null
    return { name, url }
  }

  return null
}

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

  const isPrimitive = (val: any) => ['string', 'number', 'boolean'].includes(typeof val)
  const toLabel = (val: any): string | null => {
    const opt = options.find((item) => {
      if (item.value === val) return true
      if (!isPrimitive(item.value) || !isPrimitive(val)) return false
      return String(item.value) === String(val)
    })
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
    case 'year':
      return formatDate(value, props.field.dateFormat || 'YYYY')
    case 'month':
      return formatDate(value, props.field.dateFormat || 'YYYY-MM')
    case 'daterange': {
      const rawRange = Array.isArray(value)
        ? value
        : (typeof value === 'string' && value.includes(',')) ? value.split(',') : []
      if (rawRange.length < 2) return safeText(value)
      const fmt = props.field.dateFormat || 'YYYY-MM-DD'
      const start = formatDate(rawRange[0], fmt)
      const end = formatDate(rawRange[1], fmt)
      return `${start} ~ ${end}`
    }
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
  const dynamicTag = typeof props.field.tagType === 'function'
    ? props.field.tagType(raw)
    : props.field.tagType?.[String(raw)]
  return dynamicTag || option?.color || props.field.defaultTagType || 'info'
})

const linkHref = computed(() => {
  if (displayType.value !== 'link' || !props.field.href || !hasValue.value) return ''
  return props.field.href.replace('{value}', String(props.value))
})

const normalizeImageSrc = (item: any): string => {
  return resolveImageUrlFromValue(item)
}

const imageList = computed(() => {
  if (!hasValue.value) return []
  const raw = Array.isArray(props.value) ? props.value : [props.value]
  return raw.map(normalizeImageSrc).filter(Boolean)
})

const booleanValue = computed<boolean | null>(() => {
  const value = props.value
  if (value === true || value === false) return value
  if (value === 1 || value === 0) return value === 1
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'y'].includes(normalized)) return true
    if (['false', '0', 'no', 'n'].includes(normalized)) return false
  }
  return null
})

const booleanText = computed(() => {
  if (booleanValue.value === null) return safeText(props.value)
  return booleanValue.value ? t('common.yes') : t('common.no')
})

const booleanTagType = computed(() => {
  if (booleanValue.value === null) return 'info'
  return booleanValue.value ? 'success' : 'info'
})

const colorText = computed(() => {
  const value = safeText(props.value).trim()
  return value || '-'
})

const rateValue = computed(() => {
  const num = Number(props.value)
  if (Number.isNaN(num)) return 0
  return Math.max(0, Math.min(5, num))
})

const parseMaybeJson = (value: any): any => {
  if (typeof value !== 'string') return value
  const raw = value.trim()
  if (!raw) return value
  if (!(raw.startsWith('{') || raw.startsWith('['))) return value
  try {
    return JSON.parse(raw)
  } catch {
    return value
  }
}

const toFileEntry = (value: any): FileEntry | null => {
  return resolveFileEntryFromValue(value)
}

const collectFileEntries = (value: any): FileEntry[] => {
  if (!value) return []
  if (Array.isArray(value)) {
    return value.flatMap((item) => collectFileEntries(item))
  }

  const parsed = parseMaybeJson(value)
  if (parsed !== value) return collectFileEntries(parsed)

  const objectValue = parsed as Record<string, any>
  if (objectValue && typeof objectValue === 'object') {
    const nested = objectValue.files || objectValue.items || objectValue.list
    if (Array.isArray(nested)) return collectFileEntries(nested)
  }

  const single = toFileEntry(parsed)
  return single ? [single] : []
}

const fileEntries = computed<FileEntry[]>(() => collectFileEntries(props.value))

watch(
  () => [isReferenceDisplay.value, referenceObjectCode.value, referenceIds.value.slice().sort().join(',')],
  async () => {
    if (!isReferenceDisplay.value) return
    if (!referenceObjectCode.value) return
    const ids = referenceIds.value
    if (!ids.length) return

    const missingIds = ids.filter((id) => !referenceValueMap.value[id] && !referenceValueFromInput.value[id])
    if (!missingIds.length) return

    if (props.deferReferenceResolve) {
      const needsHydration = missingIds.some((id) => {
        const inputValue = referenceValueFromInput.value[id]
        const inputLabel = resolveReferenceLabel(inputValue, referenceDisplayField.value)
        return !inputLabel || inputLabel === id
      })
      if (!needsHydration) return
    }

    const token = referenceRequestToken.value + 1
    referenceRequestToken.value = token

    try {
      const resolved = await referenceResolver.resolveMany(referenceObjectCode.value, missingIds)
      if (referenceRequestToken.value !== token) return
      referenceValueMap.value = {
        ...referenceValueMap.value,
        ...resolved
      }
    } catch (error) {
      console.warn('Failed to resolve reference field display values:', error)
    }
  },
  { immediate: true }
)

watch(
  () => [displayType.value, props.value],
  async () => {
    if (!['file', 'attachment', 'image'].includes(displayType.value)) return

    const ids = new Set<string>()
    collectCandidateFileIds(props.value, ids)
    if (ids.size === 0) return

    const missingIds = Array.from(ids).filter((id) => !fileMetadataMap.value[id])
    if (missingIds.length === 0) return

    const token = metadataRequestToken.value + 1
    metadataRequestToken.value = token

    try {
      const files = await systemFileApi.getMetadata(missingIds)
      if (metadataRequestToken.value !== token) return

      const nextMap = { ...fileMetadataMap.value }
      files.forEach((file) => {
        nextMap[file.id] = file
      })
      fileMetadataMap.value = nextMap
    } catch (error) {
      console.error('Failed to load file metadata for field display:', error)
    }
  },
  { immediate: true, deep: true }
)

const getRichTextRaw = (value: any): string => {
  if (value === undefined || value === null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'object') {
    return String(value.html || value.content || value.text || value.value || '')
  }
  return String(value)
}

const sanitizeRichText = (html: string): string => {
  const raw = String(html || '').trim()
  if (!raw) return ''
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') return raw

  const parser = new DOMParser()
  const doc = parser.parseFromString(raw, 'text/html')
  const blockedSelectors = ['script', 'style', 'iframe', 'object', 'embed', 'link', 'meta']
  doc.querySelectorAll(blockedSelectors.join(',')).forEach((node) => node.remove())
  doc.querySelectorAll('*').forEach((node) => {
    for (const attr of Array.from(node.attributes)) {
      const attrName = attr.name.toLowerCase()
      const attrValue = attr.value || ''
      if (attrName.startsWith('on')) {
        node.removeAttribute(attr.name)
        continue
      }
      if ((attrName === 'href' || attrName === 'src') && attrValue.trim().toLowerCase().startsWith('javascript:')) {
        node.removeAttribute(attr.name)
      }
    }
  })
  return doc.body.innerHTML
}

const richTextHtml = computed(() => sanitizeRichText(getRichTextRaw(props.value)))

const extractSubTableRows = (value: any): Array<Record<string, any>> => {
  if (!value) return []
  const parsed = parseMaybeJson(value)

  const asRows = (rows: any[]): Array<Record<string, any>> => {
    return rows
      .map((row) => {
        if (row && typeof row === 'object' && !Array.isArray(row)) return row
        return { value: row }
      })
      .filter((row) => !!row)
  }

  if (Array.isArray(parsed)) return asRows(parsed)
  if (parsed && typeof parsed === 'object') {
    for (const key of ['rows', 'data', 'items', 'list', 'value']) {
      if (Array.isArray((parsed as any)[key])) return asRows((parsed as any)[key])
    }
  }
  return []
}

const subTableRows = computed(() => extractSubTableRows(props.value))
const subTableTotalRows = computed(() => subTableRows.value.length)
const subTablePreviewRows = computed(() => subTableRows.value.slice(0, 5))

const subTableColumns = computed<SubTableColumn[]>(() => {
  const fieldProps = props.field.componentProps || {}
  const rawColumns = Array.isArray(fieldProps.columns) ? fieldProps.columns : []
  const fromConfig = rawColumns
    .map((column: any) => {
      const key = String(column.key || column.prop || column.code || column.field || column.fieldCode || '').trim()
      if (!key) return null
      const label = String(column.label || column.name || key)
      return { key, label }
    })
    .filter((column: SubTableColumn | null): column is SubTableColumn => !!column)

  if (fromConfig.length > 0) return fromConfig.slice(0, 6)
  const firstRow = subTableRows.value[0] || {}
  return Object.keys(firstRow)
    .slice(0, 6)
    .map((key) => ({ key, label: key }))
})

const formatSubTableCell = (row: Record<string, any>, key: string): string => {
  return safeText(row?.[key])
}

const jsonDisplay = computed(() => {
  const parsed = parseMaybeJson(props.value)
  if (parsed === undefined || parsed === null || parsed === '') return '-'
  if (typeof parsed === 'string') return parsed
  try {
    return JSON.stringify(parsed, null, 2)
  } catch {
    return safeText(parsed)
  }
})

const extractSymbolValue = (value: any): string => {
  if (value === undefined || value === null) return ''
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.map(item => extractSymbolValue(item)).find(Boolean) || ''
  }
  if (typeof value === 'object') {
    return String(
      value.qr_code ||
      value.qrCode ||
      value.barcode ||
      value.bar_code ||
      value.value ||
      value.code ||
      value.text ||
      value.content ||
      value.name ||
      ''
    )
  }
  return String(value)
}

const symbolValue = computed(() => extractSymbolValue(props.value))

const hasCodeRenderableValue = computed(() => {
  return symbolValue.value.trim() !== '' && symbolValue.value.trim() !== '-'
})

const codeImageUrl = computed(() => {
  if (!hasCodeRenderableValue.value) return ''

  const encoded = encodeURIComponent(symbolValue.value)
  const fieldProps = props.field.componentProps || {}
  if (displayType.value === 'barcode') {
    return `https://barcode.tec-it.com/barcode.ashx?data=${encoded}&code=Code128&multiple-barcodes=false&translate-esc=false&unit=Fit&dpi=96&imagetype=Gif&rotation=0&color=%23000000&bgcolor=%23ffffff&qunit=Mm&quiet=0&quietzone=0`
  }

  const size = Number(props.field.size || fieldProps.size || 150) || 150
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encoded}`
})
</script>

<style scoped>
.detail-image {
  width: 120px;
  height: 120px;
  border-radius: 4px;
  overflow: hidden;
}

.qr-code-image {
  width: 150px;
  height: 150px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.barcode-image {
  width: 200px;
  height: 60px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
}

.color-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.color-swatch {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  border: 1px solid var(--el-border-color);
}

.file-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  line-height: 1.5;
}

.reference-read-view {
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.reference-read-item {
  display: inline-flex;
}

.reference-link {
  font-size: 14px;
  line-height: inherit;
  color: var(--el-color-primary);
  word-break: break-all;
  white-space: normal;
  text-align: left;
  display: inline-block;
}

.reference-link:hover {
  text-decoration: underline;
}

.reference-hover-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reference-hover-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.reference-hover-card__content {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.reference-hover-card__title {
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-hover-card__subtitle {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-hover-card__meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.reference-hover-card__meta-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.reference-hover-card__meta-value {
  color: var(--el-text-color-regular);
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 1px 6px;
}

.reference-hover-card__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rich-text-display {
  line-height: 1.6;
  word-break: break-word;
}

.subtable-display {
  width: 100%;
}

.subtable-table {
  width: 100%;
}

.subtable-meta {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.json-display {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 8px;
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
