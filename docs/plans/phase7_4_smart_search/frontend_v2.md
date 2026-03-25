# Phase 7.4: Smart Search - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement smart search functionality with Elasticsearch-based full-text search, autocomplete, and search history.

**Note**: This module overlaps with Phase 6's global search. Coordinated implementation required.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/search.ts

export interface SearchRequest {
  query: string
  filters?: SearchFilters
  page?: number
  pageSize?: number
}

export interface SearchFilters {
  types?: SearchType[]
  status?: string[]
  category?: string
  dateFrom?: string
  dateTo?: string
}

export enum SearchType {
  ASSETS = 'assets',
  REQUESTS = 'requests',
  TASKS = 'tasks',
  USERS = 'users',
  DEPARTMENTS = 'departments',
  DOCUMENTS = 'documents'
}

export interface SearchResult {
  type: SearchType
  typeLabel: string
  id: string
  title: string
  description?: string
  highlight?: Record<string, string[]>
  url: string
  score: number
}

export interface SearchResponse {
  query: string
  total: number
  results: SearchResult[]
  aggregations?: SearchAggregation
}

export interface SearchAggregation {
  types: Record<string, number>
  statuses: Record<string, number>
}

export interface SuggestRequest {
  prefix: string
  types?: SearchType[]
  limit?: number
}

export interface SuggestResponse {
  suggestions: Suggestion[]
}

export interface Suggestion {
  text: string
  type: SearchType
  count?: number
}

export interface SearchHistoryItem {
  id: string
  query: string
  searchedAt: string
  resultCount: number
}
```

### API Service

```typescript
// frontend/src/api/search.ts

import request from '@/utils/request'
import type {
  SearchRequest,
  SearchResponse,
  SuggestRequest,
  SuggestResponse,
  SearchHistoryItem
} from '@/types/search'

export const searchApi = {
  search(data: SearchRequest): Promise<SearchResponse> {
    return request.post('/search/', data)
  },

  suggest(data: SuggestRequest): Promise<SuggestResponse> {
    return request.post('/search/suggest/', data)
  },

  // Search History
  getHistory(params?: any): Promise<SearchHistoryItem[]> {
    return request.get('/search/history/', { params })
  },

  addToHistory(query: string, resultCount: number): Promise<void> {
    return request.post('/search/history/', { query, resultCount })
  },

  clearHistory(): Promise<void> {
    return request.delete('/search/history/')
  },

  removeFromHistory(id: string): Promise<void> {
    return request.delete(`/search/history/${id}/`)
  }
}
```

---

## Component: GlobalSearchBar

```vue
<!-- frontend/src/components/common/GlobalSearchBar.vue -->
<template>
  <div class="global-search-bar">
    <el-autocomplete
      v-model="searchQuery"
      :fetch-suggestions="querySearch"
      :trigger-on-focus="false"
      :debounce="300"
      placeholder="搜索资产、请求、任务..."
      @select="handleSelect"
      @keyup.enter="handleSearch"
      @clear="handleClear"
    >
      <template #suffix>
        <el-button
          :icon="Search"
          @click="handleSearch"
        />
      </template>
      <template #default="{ item }">
        <div class="search-suggestion">
          <span class="suggestion-text">{{ item.text }}</span>
          <el-tag v-if="item.type" size="small" type="info">
            {{ getTypeLabel(item.type) }}
          </el-tag>
        </div>
      </template>
    </el-autocomplete>

    <!-- Search Results Dialog -->
    <el-dialog
      v-model="resultsVisible"
      title="搜索结果"
      width="800px"
      :close-on-click-modal="false"
    >
      <template v-if="searchResults">
        <div class="search-summary">
          找到 <strong>{{ searchResults.total }}</strong> 条结果
          <span v-if="searchResults.aggregations?.types">
            (按类型:
            <span
              v-for="(count, type) in searchResults.aggregations.types"
              :key="type"
            >
              {{ getTypeLabel(type) }} {{ count }}
            </span>)
          </span>
        </div>

        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane
            v-for="type in Object.keys(groupedResults)"
            :key="type"
            :label="getTypeLabel(type as SearchType)"
            :name="type"
          >
            <el-table
              :data="groupedResults[type]"
              @row-click="handleResultClick"
            >
              <el-table-column prop="title" label="标题" />
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
              <el-table-column prop="score" label="相关度" width="100">
                <template #default="{ row }">
                  {{ Math.round(row.score * 100) }}%
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>

    <!-- Search History Dropdown -->
    <el-dropdown v-if="showHistory" trigger="click" @command="handleHistoryCommand">
      <el-button :icon="Clock" circle />
      <template #dropdown>
        <el-dropdown-menu>
          <div v-if="history.length === 0" class="history-empty">
            暂无搜索历史
          </div>
          <el-dropdown-item
            v-for="item in history"
            :key="item.id"
            :command="item.query"
          >
            <div class="history-item">
              <span>{{ item.query }}</span>
              <span class="history-time">{{ formatTime(item.searchedAt) }}</span>
            </div>
          </el-dropdown-item>
          <el-dropdown-item divided command="clear">
            清除历史
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { searchApi } from '@/api/search'
import type { SearchResponse, SearchResult, SearchHistoryItem, SearchType } from '@/types/search'

const router = useRouter()

const searchQuery = ref('')
const resultsVisible = ref(false)
const searchResults = ref<SearchResponse | null>(null)
const activeTab = ref('all')
const showHistory = ref(false)
const history = ref<SearchHistoryItem[]>([])

const groupedResults = computed(() => {
  if (!searchResults.value) return {}

  const grouped: Record<string, SearchResult[]> = {}

  for (const result of searchResults.value.results) {
    if (!grouped[result.type]) {
      grouped[result.type] = []
    }
    grouped[result.type].push(result)
  }

  return grouped
})

const querySearch = async (queryString: string, cb: any) => {
  if (!queryString) {
    cb([])
    return
  }

  try {
    const response = await searchApi.suggest({
      prefix: queryString,
      limit: 10
    })

    cb(response.suggestions.map(s => ({
      text: s.text,
      type: s.type,
      count: s.count
    })))
  } catch (error) {
    cb([])
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return

  try {
    const response = await searchApi.search({
      query: searchQuery.value,
      page: 1,
      pageSize: 50
    })

    searchResults.value = response
    resultsVisible.value = true

    // Save to history
    await searchApi.addToHistory(searchQuery.value, response.total)
    loadHistory()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleSelect = (item: any) => {
  searchQuery.value = item.text
  handleSearch()
}

const handleResultClick = (row: SearchResult) => {
  router.push(row.url)
  resultsVisible.value = false
}

const handleClear = () => {
  searchQuery.value = ''
  searchResults.value = null
}

const handleHistoryCommand = async (command: string) => {
  if (command === 'clear') {
    try {
      await searchApi.clearHistory()
      history.value = []
      ElMessage.success('历史记录已清除')
    } catch (error) {
      // Error handled by interceptor
    }
  } else {
    searchQuery.value = command
    handleSearch()
  }
}

const loadHistory = async () => {
  try {
    const items = await searchApi.getHistory({ limit: 10 })
    history.value = items
    showHistory.value = items.length > 0
  } catch (error) {
    // Error handled by interceptor
  }
}

const getTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    assets: '资产',
    requests: '请求',
    tasks: '任务',
    users: '用户',
    departments: '部门',
    documents: '文档'
  }
  return labelMap[type] || type
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.global-search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.global-search-bar .el-autocomplete {
  width: 400px;
}

.search-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.suggestion-text {
  flex: 1;
}

.search-summary {
  margin-bottom: 16px;
  color: var(--el-text-color-secondary);
}

.search-summary strong {
  color: var(--el-color-primary);
}

.history-item {
  display: flex;
  justify-content: space-between;
  min-width: 200px;
}

.history-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.history-empty {
  padding: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
  min-width: 150px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/search.ts` | Search type definitions |
| `frontend/src/api/search.ts` | Search API service |
| `frontend/src/components/common/GlobalSearchBar.vue` | Global search bar |
| `frontend/src/views/search/SearchPage.vue` | Full search results page |
