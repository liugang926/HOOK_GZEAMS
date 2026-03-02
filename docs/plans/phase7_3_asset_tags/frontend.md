# Phase 7.3: 资产标签系统 - 前端实现

## 1. 前端组件结构

```
frontend/src/views/tags/
├── TagGroupList.vue           # 标签组列表
├── TagGroupForm.vue           # 标签组表单
├── TagList.vue                # 标签列表
├── TagForm.vue                # 标签表单
├── TagStatistics.vue          # 标签统计
└── components/
    ├── TagSelector.vue         # 标签选择器
    ├── TagFilter.vue           # 标签筛选器
    ├── TagColorPicker.vue      # 颜色选择器
    ├── AssetTagManager.vue     # 资产标签管理
    ├── TagCard.vue             # 标签卡片
    ├── BatchTagDialog.vue      # 批量打标签对话框
    └── AutoRuleList.vue        # 自动化规则列表

frontend/src/api/tags.js       # 标签API
frontend/src/composables/useTags.js  # 标签相关Hook
```

## 2. 核心组件实现

### 2.1 TagSelector（标签选择器）

```vue
<template>
  <div class="tag-selector">
    <el-select
      :model-value="modelValue"
      :multiple="multiple"
      :collapse-tags="collapseTags"
      :collapse-tags-tooltip="collapseTagsTooltip"
      :placeholder="placeholder"
      :disabled="disabled"
      @change="handleChange"
      :clearable="clearable"
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
          :disabled="!tag.is_active"
        >
          <div class="tag-option">
            <span
              class="tag-color"
              :style="{ backgroundColor: tag.color || group.color }"
            ></span>
            <span class="tag-name">{{ tag.name }}</span>
            <span class="tag-count" v-if="showCount">({{ tag.asset_count }})</span>
          </div>
        </el-option>
      </el-option-group>
    </el-select>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Array, String, Number],
    default: () => []
  },
  tagGroups: {
    type: Array,
    default: () => []
  },
  tags: {
    type: Array,
    default: () => []
  },
  multiple: {
    type: Boolean,
    default: true
  },
  collapseTags: {
    type: Boolean,
    default: true
  },
  collapseTagsTooltip: {
    type: Boolean,
    default: true
  },
  showCount: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  placeholder: {
    type: String,
    default: '请选择标签'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 如果传了tagGroups则按组分组，否则使用tags
const groupedTags = computed(() => {
  if (props.tagGroups.length > 0) {
    return props.tagGroups.map(group => ({
      ...group,
      tags: (group.tags || []).filter(tag => tag.is_active)
    }))
  }
  // 按标签组分组
  const groups = {}
  props.tags.forEach(tag => {
    if (!tag.is_active) return
    if (!groups[tag.tag_group]) {
      groups[tag.tag_group] = {
        id: tag.tag_group,
        name: tag.group_name,
        color: tag.group_color,
        tags: []
      }
    }
    groups[tag.tag_group].tags.push(tag)
  })
  return Object.values(groups)
})

const handleChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped lang="scss">
.tag-selector {
  width: 100%;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;

  .tag-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .tag-name {
    flex: 1;
  }

  .tag-count {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }
}
</style>
```

### 2.2 TagFilter（标签筛选器）

```vue
<template>
  <div class="tag-filter">
    <div class="filter-header">
      <span class="title">标签筛选</span>
      <div class="actions">
        <el-button link size="small" @click="handleExpand" v-if="!expanded">
          展开
          <el-icon><ArrowDown /></el-icon>
        </el-button>
        <el-button link size="small" @click="handleCollapse" v-else>
          收起
          <el-icon><ArrowUp /></el-icon>
        </el-button>
        <el-button link size="small" @click="handleClear" :disabled="!hasSelected">
          清空
        </el-button>
        <el-button type="primary" link size="small" @click="handleApply">
          应用
        </el-button>
      </div>
    </div>

    <div class="filter-body" v-show="expanded">
      <div
        v-for="group in tagGroups"
        :key="group.id"
        class="filter-group"
      >
        <div class="group-header">
          <span
            class="group-color"
            :style="{ backgroundColor: group.color }"
          ></span>
          <span class="group-name">{{ group.name }}</span>
          <span class="group-count">({{ getSelectedCount(group) }}/{{ group.tags?.length || 0 }})</span>
        </div>
        <div class="group-tags">
          <el-checkbox
            v-for="tag in group.tags"
            :key="tag.id"
            :model-value="selectedTags.includes(tag.id)"
            @change="handleTagChange(tag.id)"
            :disabled="!tag.is_active"
          >
            <span
              class="tag-label"
              :style="{
                backgroundColor: tag.color || group.color,
                color: getTextColor(tag.color || group.color)
              }"
            >
              {{ tag.name }}
            </span>
            <span class="asset-count">({{ tag.asset_count || 0 }})</span>
          </el-checkbox>
        </div>
      </div>
    </div>

    <!-- 已选标签展示 -->
    <div class="selected-tags" v-if="hasSelected && !expanded">
      <el-tag
        v-for="tagId in selectedTags"
        :key="tagId"
        :color="getTagById(tagId)?.color"
        closable
        @close="handleTagChange(tagId)"
        size="small"
      >
        {{ getTagById(tagId)?.name }}
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const props = defineProps({
  tagGroups: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['change'])

const expanded = ref(true)
const selectedTags = ref([])

const hasSelected = computed(() => selectedTags.value.length > 0)

const getSelectedCount = (group) => {
  if (!group.tags) return 0
  return group.tags.filter(tag => selectedTags.value.includes(tag.id)).length
}

const getTagById = (tagId) => {
  for (const group of props.tagGroups) {
    const tag = group.tags?.find(t => t.id === tagId)
    if (tag) return tag
  }
  return null
}

const getTextColor = (bgColor) => {
  // 简单判断背景色深浅返回文字颜色
  const hex = bgColor.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  return brightness > 128 ? '#000' : '#fff'
}

const handleTagChange = (tagId) => {
  const index = selectedTags.value.indexOf(tagId)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tagId)
  }
}

const handleClear = () => {
  selectedTags.value = []
  emit('change', [])
}

const handleApply = () => {
  emit('change', selectedTags.value)
}

const handleExpand = () => {
  expanded.value = true
}

const handleCollapse = () => {
  expanded.value = false
}

// 暴露方法给父组件
defineExpose({
  clear: handleClear,
  getSelected: () => selectedTags.value
})
</script>

<style scoped lang="scss">
.tag-filter {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  background: var(--el-bg-color);

  .filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .title {
      font-weight: 500;
      font-size: 14px;
    }

    .actions {
      display: flex;
      gap: 8px;
    }
  }

  .filter-body {
    .filter-group {
      margin-bottom: 16px;

      &:last-child {
        margin-bottom: 0;
      }

      .group-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: 500;

        .group-color {
          width: 8px;
          height: 8px;
          border-radius: 2px;
        }

        .group-count {
          color: var(--el-text-color-secondary);
          font-size: 12px;
        }
      }

      .group-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding-left: 14px;

        :deep(.el-checkbox) {
          margin-right: 0;
        }

        .tag-label {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .asset-count {
          color: var(--el-text-color-secondary);
          font-size: 11px;
          margin-left: 4px;
        }
      }
    }
  }

  .selected-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }
}
</style>
```

### 2.3 AssetTagManager（资产标签管理）

```vue
<template>
  <div class="asset-tag-manager">
    <!-- 资产列表中的标签展示 -->
    <template v-if="mode === 'list'">
      <el-space wrap>
        <el-tag
          v-for="tag in displayTags"
          :key="tag.id"
          :color="tag.color"
          size="small"
          closable
          @close="handleRemoveTag(tag)"
          disable-transitions
        >
          {{ tag.name }}
        </el-tag>
        <el-tag
          v-if="canEdit && tags.length < maxTags"
          type="info"
          size="small"
          @click="showAddDialog = true"
          style="cursor: pointer"
        >
          + 添加
        </el-tag>
      </el-space>
    </template>

    <!-- 表单中的标签选择 -->
    <template v-else-if="mode === 'form'">
      <TagSelector
        v-model="selectedTagIds"
        :tag-groups="tagGroups"
        :multiple="true"
        placeholder="选择标签"
        @change="handleTagChange"
      />
      <div class="tag-limit-tip" v-if="selectedTagIds.length >= maxTags">
        <el-text type="warning" size="small">
          最多可选择{{ maxTags }}个标签
        </el-text>
      </div>
    </template>

    <!-- 添加标签对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加标签"
      width="500px"
      :close-on-click-modal="false"
    >
      <TagSelector
        v-model="dialogSelectedTags"
        :tag-groups="availableTagGroups"
        :multiple="true"
        placeholder="选择要添加的标签"
      />
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAdd" :disabled="!canAddMore">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量打标签对话框 -->
    <el-dialog
      v-model="showBatchDialog"
      title="批量打标签"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        已选择 <strong>{{ selectedAssets.length }}</strong> 项资产
      </el-alert>

      <TagSelector
        v-model="batchTagIds"
        :tag-groups="tagGroups"
        :multiple="true"
        placeholder="选择标签"
      />

      <el-input
        v-model="batchNotes"
        type="textarea"
        :rows="2"
        placeholder="备注说明（可选）"
        style="margin-top: 12px"
      />

      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBatchAdd" :loading="batchLoading">
          确定添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import TagSelector from './TagSelector.vue'
import { addAssetTag, removeAssetTag, batchAddTags } from '@/api/tags'

const props = defineProps({
  assetId: {
    type: String,
    default: ''
  },
  tags: {
    type: Array,
    default: () => []
  },
  tagGroups: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: 'list', // list | form
  },
  canEdit: {
    type: Boolean,
    default: true
  },
  maxTags: {
    type: Number,
    default: 20
  }
})

const emit = defineEmits(['update:tags', 'change'])

const selectedTagIds = ref([])
const showAddDialog = ref(false)
const dialogSelectedTags = ref([])
const showBatchDialog = ref(false)
const selectedAssets = ref([])
const batchTagIds = ref([])
const batchNotes = ref('')
const batchLoading = ref(false)

// 计算属性
const displayTags = computed(() => {
  return props.tags.slice(0, 5) // 列表模式最多显示5个
})

const availableTagGroups = computed(() => {
  // 过滤掉已有的标签
  const existingTagIds = props.tags.map(t => t.id)
  return props.tagGroups.map(group => ({
    ...group,
    tags: (group.tags || []).filter(tag =>
      !existingTagIds.includes(tag.id) && tag.is_active
    )
  })).filter(group => group.tags.length > 0)
})

const canAddMore = computed(() => {
  return props.tags.length + dialogSelectedTags.value.length <= props.maxTags
})

// 初始化选中的标签ID
watch(() => props.tags, (newTags) => {
  selectedTagIds.value = newTags.map(t => t.id)
}, { immediate: true })

// 方法
const handleTagChange = (tagIds) => {
  emit('update:tags', tagIds)
  emit('change', tagIds)
}

const handleRemoveTag = async (tag) => {
  if (!props.assetId) {
    // 本地移除
    const newTags = props.tags.filter(t => t.id !== tag.id)
    emit('update:tags', newTags)
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要移除标签"${tag.name}"吗？`,
      '确认操作',
      { type: 'warning' }
    )

    await removeAssetTag(props.assetId, tag.id)
    ElMessage.success('标签移除成功')

    const newTags = props.tags.filter(t => t.id !== tag.id)
    emit('update:tags', newTags)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '标签移除失败')
    }
  }
}

const handleConfirmAdd = async () => {
  if (!props.assetId) {
    // 本地添加
    const newTagIds = [...selectedTagIds.value, ...dialogSelectedTags.value]
    emit('update:tags', newTagIds)
    showAddDialog.value = false
    dialogSelectedTags.value = []
    return
  }

  try {
    for (const tagId of dialogSelectedTags.value) {
      await addAssetTag(props.assetId, { tag_id: tagId })
    }
    ElMessage.success(`成功添加${dialogSelectedTags.value.length}个标签`)

    // 更新本地tags
    selectedTagIds.value.push(...dialogSelectedTags.value)
    showAddDialog.value = false
    dialogSelectedTags.value = []
    emit('change')
  } catch (error) {
    ElMessage.error(error.message || '标签添加失败')
  }
}

const handleBatchAdd = async () => {
  if (batchTagIds.value.length === 0) {
    ElMessage.warning('请选择标签')
    return
  }

  batchLoading.value = true
  try {
    const assetIds = selectedAssets.value.map(a => a.id)
    await batchAddTags({
      asset_ids: assetIds,
      tag_ids: batchTagIds.value,
      notes: batchNotes.value
    })

    ElMessage.success(`成功为${assetIds.length}项资产添加标签`)
    showBatchDialog.value = false
    batchTagIds.value = []
    batchNotes.value = ''
    emit('batch-complete')
  } catch (error) {
    ElMessage.error(error.message || '批量打标签失败')
  } finally {
    batchLoading.value = false
  }
}

// 暴露方法
defineExpose({
  openBatchDialog: (assets) => {
    selectedAssets.value = assets
    showBatchDialog.value = true
  }
})
</script>

<style scoped lang="scss">
.asset-tag-manager {
  .tag-limit-tip {
    margin-top: 4px;
  }
}
</style>
```

### 2.4 TagStatistics（标签统计）

```vue
<template>
  <div class="tag-statistics">
    <div class="stats-header">
      <h3>标签统计</h3>
      <el-select
        v-model="selectedGroup"
        placeholder="全部标签组"
        clearable
        style="width: 200px"
        @change="handleGroupChange"
      >
        <el-option
          v-for="group in tagGroups"
          :key="group.id"
          :label="group.name"
          :value="group.id"
        />
      </el-select>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ statistics.total_tagged_assets }}</div>
        <div class="stat-label">已打标签资产</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statistics.total_tags }}</div>
        <div class="stat-label">标签总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statistics.total_groups }}</div>
        <div class="stat-label">标签组数</div>
      </div>
    </div>

    <!-- 标签使用排行 -->
    <div class="tag-rankings">
      <h4>标签使用排行</h4>
      <div class="ranking-list">
        <div
          v-for="(item, index) in sortedTags"
          :key="item.id"
          class="ranking-item"
        >
          <div class="rank" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
          <div class="tag-info">
            <span
              class="tag-color"
              :style="{ backgroundColor: item.color }"
            ></span>
            <span class="tag-name">{{ item.name }}</span>
            <span class="group-name">{{ item.group_name }}</span>
          </div>
          <div class="tag-stats">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{
                  width: item.percentage + '%',
                  backgroundColor: item.color
                }"
              ></div>
            </div>
            <span class="count">{{ item.asset_count }}</span>
            <span class="percentage">{{ item.percentage }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 标签组分布图 -->
    <div class="group-distribution">
      <h4>标签组分布</h4>
      <div class="distribution-chart">
        <div
          v-for="group in groupDistribution"
          :key="group.id"
          class="distribution-item"
        >
          <div class="group-header">
            <span
              class="group-color"
              :style="{ backgroundColor: group.color }"
            ></span>
            <span class="group-name">{{ group.name }}</span>
            <span class="group-count">{{ group.asset_count }}</span>
          </div>
          <div class="group-progress">
            <div
              class="progress-fill"
              :style="{
                width: group.percentage + '%',
                backgroundColor: group.color
              }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTagStatistics, getTagGroups } from '@/api/tags'

const props = defineProps({
  autoLoad: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['loaded'])

const tagGroups = ref([])
const statistics = ref({
  total_tagged_assets: 0,
  total_tags: 0,
  total_groups: 0,
  tag_statistics: []
})
const selectedGroup = ref(null)

const sortedTags = computed(() => {
  return statistics.value.tag_statistics
    .sort((a, b) => b.asset_count - a.asset_count)
    .slice(0, 10)
})

const groupDistribution = computed(() => {
  const groups = {}
  statistics.value.tag_statistics.forEach(tag => {
    if (!groups[tag.tag_group]) {
      groups[tag.tag_group] = {
        id: tag.tag_group,
        name: tag.group_name,
        color: tag.group_color,
        asset_count: 0
      }
    }
    groups[tag.tag_group].asset_count += tag.asset_count
  })

  const total = statistics.value.total_tagged_assets || 1
  return Object.values(groups).map(g => ({
    ...g,
    percentage: Math.round(g.asset_count / total * 100)
  })).sort((a, b) => b.asset_count - a.asset_count)
})

const loadStatistics = async () => {
  try {
    const [statsRes, groupsRes] = await Promise.all([
      getTagStatistics({ tag_group: selectedGroup.value }),
      getTagGroups({ is_active: true })
    ])

    statistics.value = statsRes.data
    tagGroups.value = groupsRes.data.results
    emit('loaded', statistics.value)
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const handleGroupChange = () => {
  loadStatistics()
}

onMounted(() => {
  if (props.autoLoad) {
    loadStatistics()
  }
})

defineExpose({
  load: loadStatistics,
  refresh: loadStatistics
})
</script>

<style scoped lang="scss">
.tag-statistics {
  padding: 20px;

  .stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
    }
  }

  .stats-overview {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;

    .stat-card {
      background: var(--el-bg-color);
      border: 1px solid var(--el-border-color);
      border-radius: 8px;
      padding: 20px;
      text-align: center;

      .stat-value {
        font-size: 32px;
        font-weight: 600;
        color: var(--el-color-primary);
        margin-bottom: 8px;
      }

      .stat-label {
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
    }
  }

  .tag-rankings, .group-distribution {
    background: var(--el-bg-color);
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;

    h4 {
      margin: 0 0 16px;
      font-size: 16px;
      font-weight: 500;
    }
  }

  .ranking-list {
    .ranking-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .rank {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        background: var(--el-fill-color-light);

        &.rank-1 {
          background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
          color: #8b5a00;
        }

        &.rank-2 {
          background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
          color: #5a5a5a;
        }

        &.rank-3 {
          background: linear-gradient(135deg, #cd7f32 0%, #e5a55d 100%);
          color: #5a3a00;
        }
      }

      .tag-info {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 8px;

        .tag-color {
          width: 12px;
          height: 12px;
          border-radius: 2px;
        }

        .tag-name {
          font-weight: 500;
        }

        .group-name {
          color: var(--el-text-color-secondary);
          font-size: 12px;
        }
      }

      .tag-stats {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        max-width: 200px;

        .progress-bar {
          flex: 1;
          height: 6px;
          background: var(--el-fill-color-light);
          border-radius: 3px;
          overflow: hidden;

          .progress-fill {
            height: 100%;
            transition: width 0.3s;
          }
        }

        .count {
          font-weight: 600;
          min-width: 40px;
          text-align: right;
        }

        .percentage {
          color: var(--el-text-color-secondary);
          font-size: 12px;
          min-width: 40px;
          text-align: right;
        }
      }
    }
  }

  .distribution-chart {
    .distribution-item {
      margin-bottom: 12px;

      &:last-child {
        margin-bottom: 0;
      }

      .group-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;

        .group-color {
          width: 10px;
          height: 10px;
          border-radius: 2px;
        }

        .group-name {
          font-weight: 500;
          font-size: 14px;
        }

        .group-count {
          margin-left: auto;
          color: var(--el-text-color-secondary);
          font-size: 12px;
        }
      }

      .group-progress {
        height: 8px;
        background: var(--el-fill-color-light);
        border-radius: 4px;
        overflow: hidden;

        .progress-fill {
          height: 100%;
          transition: width 0.3s;
        }
      }
    }
  }
}
</style>
```

### 2.5 TagColorPicker（颜色选择器）

```vue
<template>
  <div class="tag-color-picker">
    <div class="preset-colors">
      <div
        v-for="color in presetColors"
        :key="color"
        class="color-item"
        :class="{ active: modelValue === color }"
        :style="{ backgroundColor: color }"
        @click="handleSelect(color)"
      >
        <el-icon v-if="modelValue === color" class="check-icon">
          <Check />
        </el-icon>
      </div>
    </div>
    <el-color-picker
      v-model="customColor"
      :predefine="presetColors"
      size="small"
      @change="handleCustomColor"
      show-alpha
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '#409eff'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const presetColors = [
  '#409eff', // 蓝色
  '#67c23a', // 绿色
  '#e6a23c', // 橙色
  '#f56c6c', // 红色
  '#909399', // 灰色
  '#c71585', // 玫红
  '#ff69b4', // 粉红
  '#9370db', // 紫色
  '#3a8ee6', // 天蓝
  '#722ed1', // 深紫
  '#13c2c2', // 青色
  '#52c41a', // 草绿
  '#faad14', // 金黄
  '#f5222d', // 绯红
  '#fa8c16', // 橘红
  '#a0d911', // 黄绿
  '#1890ff', // 亮蓝
  '#2f54eb', // 深蓝
  '#722ed1', // 紫罗兰
  '#eb2f96'  // 洋红
]

const customColor = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  customColor.value = newVal
})

const handleSelect = (color) => {
  emit('update:modelValue', color)
  emit('change', color)
}

const handleCustomColor = (color) => {
  emit('update:modelValue', color)
  emit('change', color)
}
</script>

<style scoped lang="scss">
.tag-color-picker {
  .preset-colors {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    gap: 8px;
    margin-bottom: 12px;

    .color-item {
      width: 28px;
      height: 28px;
      border-radius: 4px;
      cursor: pointer;
      border: 2px solid transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;

      &:hover {
        transform: scale(1.1);
      }

      &.active {
        border-color: var(--el-text-color-primary);
      }

      .check-icon {
        color: #fff;
        font-size: 16px;
      }
    }
  }
}
</style>
```

## 3. API封装

```javascript
// frontend/src/api/tags.js
import request from '@/utils/request'

// 标签组
export function getTagGroups(params) {
  return request({
    url: '/tags/groups/',
    method: 'get',
    params
  })
}

export function createTagGroup(data) {
  return request({
    url: '/tags/groups/',
    method: 'post',
    data
  })
}

export function updateTagGroup(id, data) {
  return request({
    url: `/tags/groups/${id}/`,
    method: 'put',
    data
  })
}

export function deleteTagGroup(id) {
  return request({
    url: `/tags/groups/${id}/`,
    method: 'delete'
  })
}

// 标签
export function getTags(params) {
  return request({
    url: '/tags/',
    method: 'get',
    params
  })
}

export function createTag(data) {
  return request({
    url: '/tags/',
    method: 'post',
    data
  })
}

export function updateTag(id, data) {
  return request({
    url: `/tags/${id}/`,
    method: 'put',
    data
  })
}

export function deleteTag(id) {
  return request({
    url: `/tags/${id}/`,
    method: 'delete'
  })
}

export function getTagStatistics(params) {
  return request({
    url: '/tags/statistics/',
    method: 'get',
    params
  })
}

// 资产标签
export function getAssetTags(assetId) {
  return request({
    url: `/assets/${assetId}/tags/`,
    method: 'get'
  })
}

export function addAssetTag(assetId, data) {
  return request({
    url: `/assets/${assetId}/tags/`,
    method: 'post',
    data
  })
}

export function removeAssetTag(assetId, tagId) {
  return request({
    url: `/assets/${assetId}/tags/${tagId}/`,
    method: 'delete'
  })
}

export function batchAddTags(data) {
  return request({
    url: '/tags/batch-add/',
    method: 'post',
    data
  })
}

export function batchRemoveTags(data) {
  return request({
    url: '/tags/batch-remove/',
    method: 'post',
    data
  })
}

export function getAssetsByTags(data) {
  return request({
    url: '/assets/by-tags/',
    method: 'post',
    data
  })
}

// 自动化规则
export function getAutoRules(params) {
  return request({
    url: '/tags/auto-rules/',
    method: 'get',
    params
  })
}

export function createAutoRule(data) {
  return request({
    url: '/tags/auto-rules/',
    method: 'post',
    data
  })
}

export function executeAutoRule(id) {
  return request({
    url: `/tags/auto-rules/${id}/execute/`,
    method: 'post'
  })
}

// 初始化
export function initializeTags() {
  return request({
    url: '/tags/initialize/',
    method: 'post'
  })
}
```

## 4. Composable

```javascript
// frontend/src/composables/useTags.js
import { ref, computed } from 'vue'
import { getTagGroups, getTags, getTagStatistics } from '@/api/tags'

export function useTags() {
  const tagGroups = ref([])
  const tags = ref([])
  const statistics = ref(null)
  const loading = ref(false)

  const loadTagGroups = async (params = {}) => {
    try {
      loading.value = true
      const res = await getTagGroups({ ...params, is_active: true })
      tagGroups.value = res.data.results

      // 为每个标签组加载其标签
      for (const group of tagGroups.value) {
        const tagsRes = await getTags({ tag_group: group.id, is_active: true })
        group.tags = tagsRes.data.results
      }

      return tagGroups.value
    } catch (error) {
      console.error('Failed to load tag groups:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const loadTags = async (params = {}) => {
    try {
      loading.value = true
      const res = await getTags({ ...params, is_active: true })
      tags.value = res.data.results
      return tags.value
    } catch (error) {
      console.error('Failed to load tags:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const loadStatistics = async (params = {}) => {
    try {
      const res = await getTagStatistics(params)
      statistics.value = res.data
      return statistics.value
    } catch (error) {
      console.error('Failed to load statistics:', error)
      throw error
    }
  }

  const getTagById = (tagId) => {
    return tags.value.find(t => t.id === tagId)
  }

  const getTagGroupById = (groupId) => {
    return tagGroups.value.find(g => g.id === groupId)
  }

  const getTagsByGroup = (groupId) => {
    return tags.value.filter(t => t.tag_group === groupId)
  }

  const groupedTags = computed(() => {
    return tagGroups.value.map(group => ({
      ...group,
      tags: getTagsByGroup(group.id)
    }))
  })

  return {
    tagGroups,
    tags,
    statistics,
    groupedTags,
    loading,
    loadTagGroups,
    loadTags,
    loadStatistics,
    getTagById,
    getTagGroupById,
    getTagsByGroup
  }
}
```

## 5. 路由配置

```javascript
// frontend/src/router/modules/tags.js
export default {
  path: '/tags',
  name: 'Tags',
  component: () => import('@/layouts/DefaultLayout.vue'),
  meta: { title: '标签管理', icon: 'PriceTag' },
  children: [
    {
      path: '',
      name: 'TagList',
      component: () => import('@/views/tags/TagList.vue'),
      meta: { title: '标签列表', cache: true }
    },
    {
      path: 'groups',
      name: 'TagGroups',
      component: () => import('@/views/tags/TagGroupList.vue'),
      meta: { title: '标签组', cache: true }
    },
    {
      path: 'statistics',
      name: 'TagStatistics',
      component: () => import('@/views/tags/TagStatistics.vue'),
      meta: { title: '标签统计', cache: true }
    },
    {
      path: 'auto-rules',
      name: 'AutoRules',
      component: () => import('@/views/tags/AutoRuleList.vue'),
      meta: { title: '自动化规则', cache: true }
    }
  ]
}
```
