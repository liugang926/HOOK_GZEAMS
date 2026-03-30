<template>
  <div class="asset-tag-selector">
    <el-select
      class="asset-tag-selector__control"
      :model-value="normalizedValue"
      :multiple="multiple"
      :collapse-tags="collapseTags"
      :collapse-tags-tooltip="collapseTagsTooltip"
      :clearable="clearable"
      :disabled="disabled"
      :filterable="filterable"
      :loading="loading"
      :placeholder="resolvedPlaceholder"
      @change="handleChange"
    >
      <el-option-group
        v-for="group in groupedTags"
        :key="group.id"
        :label="group.name"
      >
        <el-option
          v-for="tag in group.tags"
          :key="tag.id"
          :label="tag.name"
          :value="tag.id"
        >
          <div class="asset-tag-selector__option">
            <span
              class="asset-tag-selector__swatch"
              :style="{ backgroundColor: tag.color || group.color || '#409EFF' }"
            />
            <span class="asset-tag-selector__name">{{ tag.name }}</span>
            <span
              v-if="showCount"
              class="asset-tag-selector__count"
            >
              ({{ tag.assetCount || 0 }})
            </span>
          </div>
        </el-option>
      </el-option-group>
    </el-select>

    <p
      v-if="loadError"
      class="asset-tag-selector__error"
    >
      {{ loadError }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetTagGroupApi } from '@/api/tags'
import type { AssetTagGroup, AssetTagGroupQueryParams, AssetTagSummary } from '@/types/tags'

interface TagSelectorGroup extends Omit<AssetTagGroup, 'tags'> {
  tags: AssetTagSummary[]
}

const props = withDefaults(defineProps<{
  modelValue?: string[] | string | null
  groups?: AssetTagGroup[]
  tags?: AssetTagSummary[]
  multiple?: boolean
  collapseTags?: boolean
  collapseTagsTooltip?: boolean
  clearable?: boolean
  disabled?: boolean
  filterable?: boolean
  showCount?: boolean
  placeholder?: string
  autoload?: boolean
  queryParams?: AssetTagGroupQueryParams
}>(), {
  modelValue: () => [],
  groups: () => [],
  tags: () => [],
  multiple: true,
  collapseTags: true,
  collapseTagsTooltip: true,
  clearable: true,
  disabled: false,
  filterable: true,
  showCount: false,
  placeholder: '',
  autoload: true,
  queryParams: () => ({ pageSize: 200, isActive: true }),
})

const emit = defineEmits<{
  'update:modelValue': [value: string[] | string | null]
  change: [value: string[] | string | null]
  loaded: [groups: TagSelectorGroup[]]
  error: [message: string]
}>()

const { t } = useI18n()
const loading = ref(false)
const loadError = ref('')
const loadedGroups = ref<TagSelectorGroup[]>([])

const normalizeGroups = (groups: AssetTagGroup[]): TagSelectorGroup[] =>
  groups.map((group) => ({
    ...group,
    tags: [...(group.tags || [])]
      .filter((tag) => !!tag.id)
      .sort((left, right) => left.name.localeCompare(right.name)),
  }))

const normalizeTagsToGroups = (tags: AssetTagSummary[]): TagSelectorGroup[] => {
  const groupedMap = new Map<string, TagSelectorGroup>()

  tags.forEach((tag) => {
    if (!tag.id) return
    const groupId = tag.tagGroup || 'ungrouped'
    if (!groupedMap.has(groupId)) {
      groupedMap.set(groupId, {
        id: groupId,
        name: tag.groupName || t('system.assetTagSelector.ungrouped'),
        code: groupId,
        description: '',
        color: tag.groupColor || '#409EFF',
        icon: '',
        sortOrder: 0,
        isSystem: false,
        isActive: true,
        tagsCount: 0,
        tags: [],
      })
    }

    groupedMap.get(groupId)!.tags.push(tag)
  })

  return Array.from(groupedMap.values()).map((group) => ({
    ...group,
    tagsCount: group.tags.length,
    tags: [...group.tags].sort((left, right) => left.name.localeCompare(right.name)),
  }))
}

const groupedTags = computed<TagSelectorGroup[]>(() => {
  if (props.groups.length > 0) {
    return normalizeGroups(props.groups)
  }
  if (props.tags.length > 0) {
    return normalizeTagsToGroups(props.tags)
  }
  return loadedGroups.value
})

const normalizedValue = computed<string[] | string | null>(() => {
  if (props.multiple) {
    if (Array.isArray(props.modelValue)) return props.modelValue
    if (!props.modelValue) return []
    return [props.modelValue]
  }

  if (Array.isArray(props.modelValue)) {
    return props.modelValue[0] || null
  }
  return props.modelValue || null
})

const resolvedPlaceholder = computed(() =>
  props.placeholder || t('system.assetTagSelector.placeholder')
)

const loadTagGroups = async () => {
  if (!props.autoload || props.groups.length > 0 || props.tags.length > 0) {
    return
  }

  loading.value = true
  loadError.value = ''

  try {
    const page = await assetTagGroupApi.list(props.queryParams)
    loadedGroups.value = normalizeGroups(page.results || [])
    emit('loaded', loadedGroups.value)
  } catch (error) {
    loadError.value = t('system.assetTagSelector.loadFailed')
    emit('error', loadError.value)
  } finally {
    loading.value = false
  }
}

const handleChange = (value: string[] | string | null) => {
  const normalized =
    props.multiple && !Array.isArray(value)
      ? (value ? [value] : [])
      : value

  emit('update:modelValue', normalized)
  emit('change', normalized)
}

watch(
  () => [props.groups, props.tags],
  () => {
    if (props.groups.length > 0 || props.tags.length > 0) {
      loadError.value = ''
    }
  },
  { deep: true }
)

onMounted(() => {
  loadTagGroups()
})
</script>

<style scoped lang="scss">
.asset-tag-selector {
  width: 100%;
}

.asset-tag-selector__control {
  width: 100%;
}

.asset-tag-selector__option {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.asset-tag-selector__swatch {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgb(15 23 42 / 12%);
}

.asset-tag-selector__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-tag-selector__count {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  flex-shrink: 0;
}

.asset-tag-selector__error {
  margin: 6px 0 0;
  color: var(--el-color-danger);
  font-size: 12px;
}
</style>
