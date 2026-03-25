# Phase 7.4: 智能搜索增强 - 前端实现

## 1. 前端组件结构

```
frontend/src/views/search/
├── SmartSearch.vue            # 智能搜索主页
├── SearchResultList.vue       # 搜索结果列表
├── SearchHistory.vue          # 搜索历史
├── SavedSearchList.vue        # 保存的搜索
└── components/
    ├── SmartSearchBox.vue     # 智能搜索框
    ├── SearchSuggestion.vue   # 搜索建议
    ├── AdvancedSearchDialog.vue # 高级搜索对话框
    ├── SearchFilter.vue        # 搜索筛选器
    ├── ResultHighlight.vue     # 结果高亮组件
    ├── AggregationFilter.vue   # 聚合筛选
    ├── SavedSearchDialog.vue  # 保存搜索对话框
    └── TrendingSearches.vue    # 热门搜索

frontend/src/api/search.js     # 搜索API
frontend/src/composables/useSearch.js  # 搜索相关Hook
```

## 2. 核心组件实现

### 2.1 SmartSearchBox（智能搜索框）

```vue
<template>
  <div class="smart-search-box" :class="{ 'with-filters': showFilters }">
    <el-autocomplete
      v-model="keyword"
      :fetch-suggestions="querySearch"
      :placeholder="placeholder"
      :trigger-on-focus="false"
      :debounce="300"
      :popper-class="'search-autocomplete-popper'"
      @select="handleSelect"
      @keyup.enter="handleSearch"
      clearable
      @clear="handleClear"
    >
      <template #suffix>
        <el-button
          :icon="Search"
          circle
          type="primary"
          @click="handleSearch"
        />
        <el-dropdown trigger="click" @command="handleMoreAction">
          <el-button :icon="MoreFilled" circle />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="advanced">
                <el-icon><Setting /></el-icon>
                高级搜索
              </el-dropdown-item>
              <el-dropdown-item command="save">
                <el-icon><Star /></el-icon>
                保存搜索
              </el-dropdown-item>
              <el-dropdown-item command="history">
                <el-icon><Clock /></el-icon>
                搜索历史
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template #default="{ item }">
        <div class="search-item" :class="`type-${item.type}`">
          <el-icon v-if="item.type === 'history'" class="item-icon">
            <Clock />
          </el-icon>
          <el-icon v-else-if="item.type === 'saved'" class="item-icon">
            <StarFilled />
          </el-icon>
          <el-icon v-else-if="item.type === 'trending'" class="item-icon trending">
            <TrendCharts />
          </el-icon>
          <span class="label" v-html="highlightMatch(item.label, keyword)"></span>
          <span class="count" v-if="item.count">({{ item.count }})</span>
        </div>
      </template>
    </el-autocomplete>

    <!-- 高级搜索对话框 -->
    <AdvancedSearchDialog
      v-model="showAdvancedSearch"
      :filters="currentFilters"
      @search="handleAdvancedSearch"
    />

    <!-- 保存搜索对话框 -->
    <SavedSearchDialog
      v-model="showSaveDialog"
      :keyword="keyword"
      :filters="currentFilters"
      @saved="handleSaved"
    />

    <!-- 搜索历史抽屉 -->
    <el-drawer
      v-model="showHistoryDrawer"
      title="搜索历史"
      size="400px"
    >
      <SearchHistory
        @select="handleHistorySelect"
        @clear="handleHistoryClear"
      />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, MoreFilled, Setting, Star, Clock, StarFilled,
  TrendCharts
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  searchAssets,
  getSearchSuggestions,
  getSearchHistory,
  saveSearch
} from '@/api/search'
import { useSearchStore } from '@/stores/search'
import AdvancedSearchDialog from './components/AdvancedSearchDialog.vue'
import SavedSearchDialog from './components/SavedSearchDialog.vue'
import SearchHistory from './SearchHistory.vue'

const props = defineProps({
  searchType: {
    type: String,
    default: 'asset' // asset/project/loan
  },
  placeholder: {
    type: String,
    default: '搜索资产名称、编号、规格...'
  },
  showFilters: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['search', 'filter-change'])

const router = useRouter()
const searchStore = useSearchStore()

const keyword = ref('')
const showAdvancedSearch = ref(false)
const showSaveDialog = ref(false)
const showHistoryDrawer = ref(false)
const currentFilters = ref({})
const suggestions = ref([])

// 查询建议
const querySearch = async (queryString, cb) => {
  if (!queryString) {
    // 显示热门搜索和历史
    const items = []

    // 添加历史记录
    const history = await getSearchHistory({
      type: props.searchType,
      limit: 5
    })
    history.data.forEach(item => {
      items.push({
        value: item.keyword,
        label: item.keyword,
        type: 'history',
        filters: item.filters
      })
    })

    cb(items)
    return
  }

  // 获取搜索建议
  try {
    const response = await getSearchSuggestions({
      keyword: queryString,
      type: props.searchType
    })

    const items = response.data.map(item => ({
      value: item.suggestion,
      label: item.suggestion,
      type: 'suggestion',
      count: item.count
    }))

    cb(items)
  } catch (error) {
    cb([])
  }
}

// 高亮匹配
const highlightMatch = (text, query) => {
  if (!query) return text
  const regex = new RegExp(`(${query})`, 'gi')
  return text.replace(regex, '<em>$1</em>')
}

const handleSelect = (item) => {
  if (item.type === 'history' || item.type === 'saved') {
    keyword.value = item.value
    if (item.filters) {
      currentFilters.value = item.filters
    }
    executeSearch()
  } else {
    handleSearch(item.value)
  }
}

const handleSearch = (value) => {
  const searchKeyword = value || keyword.value
  if (!searchKeyword && Object.keys(currentFilters.value).length === 0) {
    return
  }
  executeSearch()
}

const executeSearch = async () => {
  try {
    const result = await searchAssets({
      keyword: keyword.value,
      filters: currentFilters.value,
      sort_by: 'relevance',
      page: 1,
      page_size: 20
    })

    // 保存搜索历史
    searchStore.addHistory({
      type: props.searchType,
      keyword: keyword.value,
      filters: currentFilters.value,
      result_count: result.data.total
    })

    emit('search', {
      keyword: keyword.value,
      filters: currentFilters.value,
      result: result.data
    })
  } catch (error) {
    ElMessage.error(error.message || '搜索失败')
  }
}

const handleAdvancedSearch = (searchParams) => {
  currentFilters.value = searchParams.filters
  keyword.value = searchParams.keyword || keyword.value
  showAdvancedSearch.value = false
  executeSearch()
}

const handleMoreAction = (command) => {
  switch (command) {
    case 'advanced':
      showAdvancedSearch.value = true
      break
    case 'save':
      showSaveDialog.value = true
      break
    case 'history':
      showHistoryDrawer.value = true
      break
  }
}

const handleSaved = () => {
  ElMessage.success('搜索保存成功')
}

const handleHistorySelect = (item) => {
  keyword.value = item.keyword
  currentFilters.value = item.filters
  showHistoryDrawer.value = false
  executeSearch()
}

const handleHistoryClear = () => {
  ElMessage.success('搜索历史已清空')
}

const handleClear = () => {
  keyword.value = ''
  currentFilters.value = {}
  emit('filter-change', {})
}
</script>

<style scoped lang="scss">
.smart-search-box {
  width: 100%;

  :deep(.el-autocomplete) {
    width: 100%;
  }

  .el-autocomplete {
    width: 100%;
  }

  :deep(.el-input__wrapper) {
    padding-right: 80px;
  }

  :deep(.el-input__suffix) {
    display: flex;
    gap: 8px;
    right: 10px;
  }

  .search-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;

    .item-icon {
      color: var(--el-text-color-secondary);
      font-size: 16px;
    }

    .item-icon.trending {
      color: var(--el-color-danger);
    }

    .label {
      flex: 1;

      :deep(em) {
        color: var(--el-color-primary);
        font-style: normal;
        font-weight: 500;
      }
    }

    .count {
      color: var(--el-text-color-secondary);
      font-size: 12px;
    }

    &.type-history {
      .label {
        color: var(--el-text-color-regular);
      }
    }

    &.type-saved {
      .label {
        color: var(--el-color-warning);
      }
    }
  }
}
</style>
```

### 2.2 SearchResultList（搜索结果列表）

```vue
<template>
  <div class="search-result-list">
    <!-- 结果统计 -->
    <div class="result-header">
      <div class="result-summary">
        找到 <strong>{{ total }}</strong> 条相关结果
        <span v-if="searchTime" class="search-time">
          (耗时 {{ searchTime }}ms)
        </span>
      </div>

      <div class="result-actions">
        <el-radio-group v-model="sortBy" size="small" @change="handleSortChange">
          <el-radio-button label="relevance">相关度</el-radio-button>
          <el-radio-button label="date">日期</el-radio-button>
          <el-radio-button label="price">价格</el-radio-button>
        </el-radio-group>

        <el-dropdown split-button type="primary" @click="exportResults">
          导出
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="exportAs('excel')">
                导出为Excel
              </el-dropdown-item>
              <el-dropdown-item @click="exportAs('csv')">
                导出为CSV
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 结果列表 -->
    <div v-else-if="results.length > 0">
      <div
        v-for="item in results"
        :key="item.id"
        class="result-item"
        @click="handleItemClick(item)"
      >
        <div class="item-main">
          <div class="item-title">
            <span class="code">{{ item.asset_code }}</span>
            <span class="name" v-html="item.highlight.asset_name || item.asset_name"></span>
          </div>
          <div class="item-meta">
            <el-tag size="small" type="info">{{ item.category_name }}</el-tag>
            <el-tag size="small" :type="getStatusType(item.status)">
              {{ item.status_display }}
            </el-tag>
            <span class="location" v-if="item.location_name">
              <el-icon><Location /></el-icon>
              {{ item.location_name }}
            </span>
            <span class="custodian" v-if="item.custodian_name">
              <el-icon><User /></el-icon>
              {{ item.custodian_name }}
            </span>
          </div>
          <div class="item-spec" v-if="item.specification">
            {{ item.specification }}
          </div>
        </div>
        <div class="item-side">
          <div class="price" v-if="item.purchase_price">
            ¥{{ formatPrice(item.purchase_price) }}
          </div>
          <div class="score" v-if="showScore">
            <el-tooltip content="相关度评分">
              <span>{{ Math.round(item.score * 10) / 10 }}</span>
            </el-tooltip>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 无结果 -->
    <div v-else class="empty-result">
      <el-empty :description="emptyDescription">
        <template #image>
          <el-icon :size="100" color="var(--el-text-color-placeholder)">
            <Search />
          </el-icon>
        </template>
        <el-button type="primary" @click="$emit('reset')">清除筛选</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Location, User, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  },
  total: {
    type: Number,
    default: 0
  },
  page: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  loading: {
    type: Boolean,
    default: false
  },
  searchTime: {
    type: Number,
    default: null
  },
  showScore: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['search', 'page-change', 'sort-change', 'item-click', 'reset'])

const router = useRouter()
const sortBy = ref('relevance')
const currentPage = ref(props.page)
const pageSize = ref(props.pageSize)

const emptyDescription = computed(() => {
  if (props.total === 0) {
    return '未找到相关结果，请尝试其他关键词'
  }
  return '暂无搜索结果'
})

const getStatusType = (status) => {
  const map = {
    idle: '',
    in_use: 'success',
    lent_out: 'warning',
    maintenance: 'danger',
    scrapped: 'info'
  }
  return map[status] || ''
}

const formatPrice = (price) => {
  return Number(price).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const handleSortChange = () => {
  emit('sort-change', sortBy.value)
}

const handlePageChange = (page) => {
  currentPage.value = page
  emit('page-change', { page, pageSize: pageSize.value })
}

const handleSizeChange = (size) => {
  pageSize.value = size
  emit('page-change', { page: 1, pageSize: size })
}

const handleItemClick = (item) => {
  emit('item-click', item)
  // 跳转到详情页
  router.push({
    name: 'AssetDetail',
    params: { id: item.id }
  })
}

const exportResults = () => {
  ElMessage.info('导出功能开发中')
}

const exportAs = (format) => {
  ElMessage.info(`${format}导出功能开发中`)
}
</script>

<style scoped lang="scss">
.search-result-list {
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--el-border-color-lighter);

    .result-summary {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;

      strong {
        color: var(--el-color-primary);
        font-size: 18px;
      }

      .search-time {
        color: var(--el-text-color-secondary);
        font-size: 12px;
      }
    }

    .result-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
  }

  .result-item {
    display: flex;
    justify-content: space-between;
    padding: 16px;
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: var(--el-color-primary);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }

    .item-main {
      flex: 1;

      .item-title {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;

        .code {
          font-family: monospace;
          background: var(--el-fill-color-light);
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }

        .name {
          font-size: 16px;
          font-weight: 500;

          :deep(em) {
            color: var(--el-color-primary);
            font-style: normal;
            font-weight: 600;
          }
        }
      }

      .item-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 8px;

        span {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: var(--el-text-color-secondary);
        }
      }

      .item-spec {
        font-size: 13px;
        color: var(--el-text-color-secondary);
      }
    }

    .item-side {
      text-align: right;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .price {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-color-danger);
      }

      .score {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        background: var(--el-fill-color-light);
        padding: 2px 8px;
        border-radius: 10px;
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }

  .empty-result {
    padding: 60px 0;
    text-align: center;
  }
}
</style>
```

### 2.3 AggregationFilter（聚合筛选）

```vue
<template>
  <div class="aggregation-filter">
    <el-collapse v-model="activeNames">
      <el-collapse-item
        v-for="(agg, name) in aggregations"
        :key="name"
        :title="getAggTitle(name)"
      >
        <template #title>
          <span class="agg-title">{{ getAggTitle(name) }}</span>
          <span class="agg-count">({{ getAggCount(agg) }})</span>
        </template>

        <div class="agg-options">
          <el-checkbox-group
            :model-value="selectedAggs[name]"
            @change="handleAggChange(name, $event)"
          >
            <el-checkbox
              v-for="(bucket, key) in agg"
              :key="key"
              :label="key"
            >
              <span class="bucket-label">{{ getBucketLabel(name, key) }}</span>
              <span class="bucket-count">({{ bucket }})</span>
            </el-checkbox>
          </el-checkbox-group>

          <el-button
            v-if="selectedAggs[name]?.length > 0"
            link
            size="small"
            type="primary"
            @click="handleClearAgg(name)"
          >
            清空
          </el-button>
        </div>
      </el-collapse-item>

      <!-- 价格范围 -->
      <el-collapse-item
        v-if="aggregations.price_ranges"
        title="价格区间"
      >
        <div class="price-ranges">
          <el-radio-group
            :model-value="selectedPriceRange"
            @change="handlePriceChange"
          >
            <el-radio
              v-for="(count, range) in aggregations.price_ranges"
              :key="range"
              :label="range"
            >
              {{ getPriceRangeLabel(range) }} ({{ count }})
            </el-radio>
          </el-radio-group>

          <el-button
            v-if="selectedPriceRange"
            link
            size="small"
            type="primary"
            @click="handleClearPrice"
          >
            清空
          </el-button>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  aggregations: {
    type: Object,
    default: () => ({})
  },
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const activeNames = ref(['category', 'status'])
const selectedAggs = ref({})
const selectedPriceRange = ref('')

const aggTitles = {
  category: '分类',
  status: '状态',
  location: '存放位置',
  manufacturer: '厂商',
  tags: '标签'
}

watch(() => props.modelValue, (newVal) => {
  selectedAggs.value = { ...newVal }
  // 提取价格范围
  if (newVal.purchase_price_min || newVal.purchase_price_max) {
    selectedPriceRange.value = detectPriceRange(newVal.purchase_price_min, newVal.purchase_price_max)
  } else {
    selectedPriceRange.value = ''
  }
}, { deep: true })

const getAggTitle = (name) => {
  return aggTitles[name] || name
}

const getAggCount = (agg) => {
  return Object.values(agg).reduce((sum, count) => sum + count, 0)
}

const getBucketLabel = (aggName, key) => {
  // 这里可以通过API获取标签对应的名称
  return key
}

const priceRangeLabels = {
  under_1k: '1千元以下',
  '1k_to_5k': '1千-5千元',
  '5k_to_10k': '5千-1万元',
  '10k_to_50k': '1万-5万元',
  over_50k: '5万元以上'
}

const getPriceRangeLabel = (range) => {
  return priceRangeLabels[range] || range
}

const detectPriceRange = (min, max) => {
  if (!min && !max) return ''
  if (max === 1000) return 'under_1k'
  if (min === 1000 && max === 5000) return '1k_to_5k'
  if (min === 5000 && max === 10000) return '5k_to_10k'
  if (min === 10000 && max === 50000) return '10k_to_50k'
  if (min === 50000) return 'over_50k'
  return ''
}

const handleAggChange = (name, values) => {
  selectedAggs.value[name] = values
  emitChange()
}

const handleClearAgg = (name) => {
  selectedAggs.value[name] = []
  emitChange()
}

const handlePriceChange = (value) => {
  selectedPriceRange.value = value
  emitChange()
}

const handleClearPrice = () => {
  selectedPriceRange.value = ''
  emitChange()
}

const emitChange = () => {
  const filters = { ...selectedAggs.value }

  // 处理价格范围
  if (selectedPriceRange.value) {
    const range = selectedPriceRange.value
    if (range === 'under_1k') {
      filters.purchase_price_max = 1000
    } else if (range === '1k_to_5k') {
      filters.purchase_price_min = 1000
      filters.purchase_price_max = 5000
    } else if (range === '5k_to_10k') {
      filters.purchase_price_min = 5000
      filters.purchase_price_max = 10000
    } else if (range === '10k_to_50k') {
      filters.purchase_price_min = 10000
      filters.purchase_price_max = 50000
    } else if (range === 'over_50k') {
      filters.purchase_price_min = 50000
    }
  }

  emit('update:modelValue', filters)
  emit('change', filters)
}
</script>

<style scoped lang="scss">
.aggregation-filter {
  .agg-title {
    font-weight: 500;
  }

  .agg-count {
    margin-left: 8px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .agg-options {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .el-checkbox-group {
      flex-direction: column;
    }

    .el-checkbox {
      margin-right: 0;
    }

    .bucket-label {
      flex: 1;
    }

    .bucket-count {
      color: var(--el-text-color-secondary);
      font-size: 12px;
    }
  }

  .price-ranges {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .el-radio-group {
      flex-direction: column;
    }

    .el-radio {
      margin-right: 0;
    }
  }
}
</style>
```

### 2.4 AdvancedSearchDialog（高级搜索对话框）

```vue
<template>
  <el-dialog
    v-model="visible"
    title="高级搜索"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form ref="formRef" :model="formData" label-width="100px">
      <el-form-item label="关键词">
        <el-input
          v-model="formData.keyword"
          placeholder="输入搜索关键词"
          clearable
        />
      </el-form-item>

      <el-form-item label="资产分类">
        <el-cascader
          v-model="formData.category"
          :options="categoryOptions"
          :props="{ value: 'id', label: 'name' }"
          clearable
          placeholder="选择分类"
        />
      </el-form-item>

      <el-form-item label="资产状态">
        <el-select
          v-model="formData.status"
          placeholder="选择状态"
          clearable
        >
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="存放位置">
        <el-cascader
          v-model="formData.location"
          :options="locationOptions"
          :props="{ value: 'id', label: 'name' }"
          clearable
          placeholder="选择位置"
        />
      </el-form-item>

      <el-form-item label="保管人">
        <el-select
          v-model="formData.custodian"
          filterable
          remote
          reserve-keyword
          placeholder="搜索保管人"
          :remote-method="searchUsers"
          :loading="userLoading"
          clearable
        >
          <el-option
            v-for="user in userOptions"
            :key="user.id"
            :label="user.full_name || user.username"
            :value="user.id"
          />
        </el-select>
      </el-form-item>

      <el-divider>价格范围</el-divider>

      <el-form-item label="价格区间">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-input-number
              v-model="formData.purchase_price_min"
              :min="0"
              :precision="2"
              placeholder="最低价格"
              controls-position="right"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="12">
            <el-input-number
              v-model="formData.purchase_price_max"
              :min="0"
              :precision="2"
              placeholder="最高价格"
              controls-position="right"
              style="width: 100%"
            />
          </el-col>
        </el-row>
      </el-form-item>

      <el-divider>购买日期</el-divider>

      <el-form-item label="日期范围">
        <el-date-picker
          v-model="formData.purchaseDateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-divider>标签筛选</el-divider>

      <el-form-item label="标签">
        <TagSelector
          v-model="formData.tags"
          :tag-groups="tagGroups"
          :multiple="true"
          placeholder="选择标签"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleReset">重置</el-button>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import TagSelector from '@/views/tags/components/TagSelector.vue'
import { searchUsers } from '@/api/accounts'

const props = defineProps({
  modelValue: Boolean,
  filters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'search'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref()
const formData = reactive({
  keyword: '',
  category: [],
  status: '',
  location: [],
  custodian: '',
  purchase_price_min: null,
  purchase_price_max: null,
  purchaseDateRange: [],
  tags: []
})

const categoryOptions = ref([])
const locationOptions = ref([])
const statusOptions = ref([
  { label: '全部', value: '' },
  { label: '在用', value: 'in_use' },
  { label: '闲置', value: 'idle' },
  { label: '借出', value: 'lent_out' },
  { label: '维修中', value: 'maintenance' },
  { label: '已报废', value: 'scrapped' }
])

const tagGroups = ref([])
const userOptions = ref([])
const userLoading = ref(false)

watch(() => props.filters, (newFilters) => {
  Object.assign(formData, {
    keyword: newFilters.keyword || '',
    category: newFilters.category || [],
    status: newFilters.status || '',
    location: newFilters.location || [],
    custodian: newFilters.custodian || '',
    purchase_price_min: newFilters.purchase_price_min || null,
    purchase_price_max: newFilters.purchase_price_max || null,
    purchaseDateRange: [],
    tags: newFilters.tags || []
  })
}, { deep: true, immediate: true })

const searchUsers = async (query) => {
  if (!query) return
  userLoading.value = true
  try {
    const res = await searchUsers({ keyword: query })
    userOptions.value = res.data.results
  } finally {
    userLoading.value = false
  }
}

const handleReset = () => {
  Object.assign(formData, {
    keyword: '',
    category: [],
    status: '',
    location: [],
    custodian: '',
    purchase_price_min: null,
    purchase_price_max: null,
    purchaseDateRange: [],
    tags: []
  })
}

const handleSearch = () => {
  const filters = {
    keyword: formData.keyword,
    category: formData.category?.[formData.category.length - 1],
    status: formData.status,
    location: formData.location?.[formData.location.length - 1],
    custodian: formData.custodian,
    tags: formData.tags
  }

  if (formData.purchase_price_min) {
    filters.purchase_price_min = formData.purchase_price_min
  }
  if (formData.purchase_price_max) {
    filters.purchase_price_max = formData.purchase_price_max
  }
  if (formData.purchaseDateRange?.length === 2) {
    filters.purchase_date_from = formData.purchaseDateRange[0]
    filters.purchase_date_to = formData.purchaseDateRange[1]
  }

  emit('search', { filters })
  visible.value = false
}
</script>
```

### 2.5 SavedSearchDialog（保存搜索对话框）

```vue
<template>
  <el-dialog
    v-model="visible"
    title="保存搜索"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
      <el-form-item label="名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="给这个搜索起个名字"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="公开">
        <el-switch v-model="formData.is_public" />
        <div class="form-tip">
          公开后，其他用户也能看到并使用这个搜索
        </div>
      </el-form-item>

      <el-form-item label="搜索摘要">
        <div class="search-summary">
          <div v-if="keyword" class="summary-item">
            <span class="label">关键词：</span>
            <span class="value">{{ keyword }}</span>
          </div>
          <div v-if="hasFilters" class="summary-item">
            <span class="label">筛选：</span>
            <span class="value">{{ filterSummary }}</span>
          </div>
          <div v-else class="summary-item">
            <span class="value">无筛选条件</span>
          </div>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="loading">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { saveSearch } from '@/api/search'

const props = defineProps({
  modelValue: Boolean,
  keyword: {
    type: String,
    default: ''
  },
  filters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref()
const loading = ref(false)

const formData = reactive({
  name: '',
  is_public: false
})

const rules = {
  name: [
    { required: true, message: '请输入搜索名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const hasFilters = computed(() => {
  return Object.keys(props.filters).length > 0
})

const filterSummary = computed(() => {
  const summaries = []
  if (props.filters.category) summaries.push('分类筛选')
  if (props.filters.status) summaries.push('状态筛选')
  if (props.filters.location) summaries.push('位置筛选')
  if (props.filters.purchase_price_min) summaries.push('价格区间')
  return summaries.join('、')
})

const handleSave = async () => {
  await formRef.value.validate()

  loading.value = true
  try {
    await saveSearch({
      name: formData.name,
      search_type: 'asset',
      keyword: props.keyword,
      filters: props.filters,
      is_public: formData.is_public
    })

    ElMessage.success('搜索保存成功')
    emit('saved')
    visible.value = false
    formData.name = ''
    formData.is_public = false
  } catch (error) {
    if (error.error?.code === 'SAVED_SEARCH_NAME_EXISTS') {
      ElMessage.error('该名称已存在，请使用其他名称')
    } else {
      ElMessage.error(error.message || '保存失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.search-summary {
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;

  .summary-item {
    display: flex;
    gap: 8px;
    margin-bottom: 4px;

    &:last-child {
      margin-bottom: 0;
    }

    .label {
      color: var(--el-text-color-secondary);
    }

    .value {
      color: var(--el-text-color-primary);
    }
  }
}
</style>
```

## 3. API封装

```javascript
// frontend/src/api/search.js
import request from '@/utils/request'

// 搜索
export function searchAssets(data) {
  return request({
    url: '/search/assets/',
    method: 'post',
    data
  })
}

export function searchProjects(data) {
  return request({
    url: '/search/projects/',
    method: 'post',
    data
  })
}

export function searchLoans(data) {
  return request({
    url: '/search/loans/',
    method: 'post',
    data
  })
}

// 搜索建议
export function getSearchSuggestions(params) {
  return request({
    url: '/search/suggestions/',
    method: 'get',
    params
  })
}

// 搜索历史
export function getSearchHistory(params) {
  return request({
    url: '/search/history/',
    method: 'get',
    params
  })
}

export function clearSearchHistory(params) {
  return request({
    url: '/search/history/',
    method: 'delete',
    params
  })
}

// 保存的搜索
export function getSavedSearches(params) {
  return request({
    url: '/search/saved/',
    method: 'get',
    params
  })
}

export function saveSearch(data) {
  return request({
    url: '/search/save/',
    method: 'post',
    data
  })
}

export function deleteSavedSearch(id) {
  return request({
    url: `/search/saved/${id}/`,
    method: 'delete'
  })
}

export function useSavedSearch(id) {
  return request({
    url: `/search/saved/${id}/use/`,
    method: 'post'
  })
}

// 热门搜索
export function getTrendingSearches(params) {
  return request({
    url: '/search/trending/',
    method: 'get',
    params
  })
}

// 搜索配置
export function getSearchConfig() {
  return request({
    url: '/search/config/',
    method: 'get'
  })
}

// 管理接口
export function rebuildIndex(data) {
  return request({
    url: '/search/admin/reindex/',
    method: 'post',
    data
  })
}

export function getIndexStatus() {
  return request({
    url: '/search/admin/index-status/',
    method: 'get'
  })
}

export function getSearchStatistics(params) {
  return request({
    url: '/search/admin/statistics/',
    method: 'get',
    params
  })
}
```

## 4. Pinia Store

```javascript
// frontend/src/stores/search.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSearchHistory, clearSearchHistory, getTrendingSearches } from '@/api/search'

export const useSearchStore = defineStore('search', () => {
  // 状态
  const recentSearches = ref([])
  const trendingSearches = ref([])
  const loading = ref(false)

  // 历史记录
  const history = ref([])
  const maxHistory = 20

  // 方法
  const addHistory = (item) => {
    // 检查是否已存在
    const existingIndex = history.value.findIndex(
      h => h.keyword === item.keyword && h.search_type === item.search_type
    )

    if (existingIndex >= 0) {
      // 更新现有记录
      history.value[existingIndex].search_count += 1
      history.value[existingIndex].last_searched_at = new Date().toISOString()
      // 移到最前
      const item = history.value.splice(existingIndex, 1)[0]
      history.value.unshift(item)
    } else {
      // 添加新记录
      history.value.unshift({
        ...item,
        search_count: 1,
        created_at: new Date().toISOString(),
        last_searched_at: new Date().toISOString()
      })
    }

    // 限制数量
    if (history.value.length > maxHistory) {
      history.value = history.value.slice(0, maxHistory)
    }
  }

  const loadHistory = async (type = 'asset') => {
    try {
      const res = await getSearchHistory({ type, limit: 10 })
      recentSearches.value = res.data
      return res.data
    } catch (error) {
      console.error('Failed to load search history:', error)
      throw error
    }
  }

  const clearHistory = async (type = 'asset') => {
    try {
      await clearSearchHistory({ type })
      history.value = history.value.filter(h => h.search_type !== type)
      recentSearches.value = recentSearches.value.filter(h => h.search_type !== type)
    } catch (error) {
      console.error('Failed to clear search history:', error)
      throw error
    }
  }

  const loadTrending = async (type = 'asset') => {
    try {
      const res = await getTrendingSearches({ type, limit: 10 })
      trendingSearches.value = res.data
      return res.data
    } catch (error) {
      console.error('Failed to load trending searches:', error)
      throw error
    }
  }

  // 获取器
  const historyByType = computed(() => (type) => {
    return history.value.filter(h => h.search_type === type)
  })

  return {
    // 状态
    recentSearches,
    trendingSearches,
    loading,
    history,

    // 方法
    addHistory,
    loadHistory,
    clearHistory,
    loadTrending,
    historyByType
  }
})
```

## 5. Composable

```javascript
// frontend/src/composables/useSearch.js
import { ref } from 'vue'
import { searchAssets, getSearchSuggestions } from '@/api/search'
import { useSearchStore } from '@/stores/search'

export function useSearch(options = {}) {
  const {
    searchType = 'asset',
    autoLoadTrending = true
  } = options

  const searchStore = useSearchStore()

  const keyword = ref('')
  const filters = ref({})
  const sortBy = ref('relevance')
  const sortOrder = ref('desc')
  const page = ref(1)
  const pageSize = ref(20)

  const results = ref([])
  const total = ref(0)
  const aggregations = ref({})
  const loading = ref(false)
  const searchTime = ref(null)

  const suggestions = ref([])

  // 执行搜索
  const executeSearch = async () => {
    loading.value = true
    const startTime = Date.now()

    try {
      const response = await searchAssets({
        keyword: keyword.value,
        filters: filters.value,
        sort_by: sortBy.value,
        sort_order: sortOrder.value,
        page: page.value,
        page_size: pageSize.value
      })

      results.value = response.data.results
      total.value = response.data.total
      aggregations.value = response.data.aggregations
      searchTime.value = Date.now() - startTime

      // 保存历史
      if (keyword.value || Object.keys(filters.value).length > 0) {
        searchStore.addHistory({
          search_type: searchType,
          keyword: keyword.value,
          filters: filters.value,
          result_count: total.value
        })
      }
    } catch (error) {
      console.error('Search failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 加载建议
  const loadSuggestions = async (query) => {
    if (!query || query.length < 1) {
      suggestions.value = []
      return
    }

    try {
      const response = await getSearchSuggestions({
        keyword: query,
        type: searchType
      })
      suggestions.value = response.data
    } catch (error) {
      console.error('Failed to load suggestions:', error)
    }
  }

  // 重置搜索
  const resetSearch = () => {
    keyword.value = ''
    filters.value = {}
    sortBy.value = 'relevance'
    sortOrder.value = 'desc'
    page.value = 1
    results.value = []
    total.value = 0
    aggregations.value = {}
  }

  // 更新筛选
  const updateFilter = (key, value) => {
    if (value === null || value === undefined || value === '') {
      delete filters.value[key]
    } else {
      filters.value[key] = value
    }
    page.value = 1
  }

  // 更新排序
  const updateSort = (field, order) => {
    sortBy.value = field
    sortOrder.value = order
    page.value = 1
  }

  return {
    // 状态
    keyword,
    filters,
    sortBy,
    sortOrder,
    page,
    pageSize,
    results,
    total,
    aggregations,
    loading,
    searchTime,
    suggestions,

    // 方法
    executeSearch,
    loadSuggestions,
    resetSearch,
    updateFilter,
    updateSort
  }
}
```

## 6. 路由配置

```javascript
// frontend/src/router/modules/search.js
export default {
  path: '/search',
  name: 'Search',
  component: () => import('@/layouts/DefaultLayout.vue'),
  meta: { title: '智能搜索', icon: 'Search' },
  children: [
    {
      path: '',
      name: 'SmartSearch',
      component: () => import('@/views/search/SmartSearch.vue'),
      meta: { title: '智能搜索', cache: false }
    },
    {
      path: 'history',
      name: 'SearchHistory',
      component: () => import('@/views/search/SearchHistory.vue'),
      meta: { title: '搜索历史', cache: false }
    },
    {
      path: 'saved',
      name: 'SavedSearch',
      component: () => import('@/views/search/SavedSearchList.vue'),
      meta: { title: '保存的搜索', cache: true }
    }
  ]
}
```
