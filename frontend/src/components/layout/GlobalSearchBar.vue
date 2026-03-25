<!--
  GlobalSearchBar — Cross-object search in the top header.

  Features:
  - Ctrl+K / ⌘+K quick focus
  - 300ms debounce, min 2 chars
  - Results grouped by object type with ObjectAvatar
  - Keyboard navigation ↑/↓/Enter/Esc
  - Recent search history (localStorage)
-->

<template>
  <div
    ref="containerRef"
    class="global-search"
    :class="{ 'is-focused': isFocused }"
  >
    <el-input
      ref="inputRef"
      v-model="keyword"
      :placeholder="t('common.placeholders.globalSearch', '搜索所有记录...')"
      prefix-icon="Search"
      clearable
      size="default"
      class="global-search__input"
      @focus="handleFocus"
      @blur="handleBlur"
      @input="handleInput"
      @keydown="handleKeydown"
    />

    <!-- Dropdown panel -->
    <transition name="search-dropdown">
      <div
        v-if="showDropdown"
        class="global-search__dropdown"
      >
        <!-- Loading -->
        <div
          v-if="isSearching"
          class="global-search__loading"
        >
          <el-skeleton
            animated
            :rows="3"
          />
        </div>

        <!-- Results -->
        <template v-else-if="hasResults">
          <div
            v-for="group in searchResults"
            :key="group.object_code"
            class="global-search__group"
          >
            <div class="global-search__group-header">
              <ObjectAvatar
                :object-code="group.object_code"
                size="sm"
              />
              <span class="global-search__group-name">{{ group.object_name }}</span>
              <el-tag
                size="small"
                type="info"
                effect="plain"
              >
                {{ group.matches.length }}
              </el-tag>
            </div>
            <div
              v-for="(match, matchIdx) in group.matches"
              :key="match.record_id"
              class="global-search__item"
              :class="{ 'is-active': isItemActive(group.object_code, matchIdx) }"
              @mouseenter="setActiveItem(group.object_code, matchIdx)"
              @click="navigateToRecord(group.object_code, match.record_id)"
            >
              <div class="global-search__item-name">
                {{ match.display_name }}
              </div>
              <div class="global-search__item-match">
                <span class="global-search__item-field">{{ match.match_field }}</span>
                <span class="global-search__item-value">{{ match.match_value }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- No results -->
        <div
          v-else-if="keyword.trim().length >= 2 && !isSearching"
          class="global-search__empty"
        >
          {{ t('common.messages.noSearchResults', '未找到匹配结果') }}
        </div>

        <!-- Recent searches (when input is empty or < 2 chars) -->
        <template v-else-if="recentSearches.length > 0">
          <div class="global-search__section-header">
            <span>{{ t('common.labels.recentSearches', '最近搜索') }}</span>
            <el-button
              type="primary"
              link
              size="small"
              @click.stop="clearHistory"
            >
              {{ t('common.actions.clear', '清除') }}
            </el-button>
          </div>
          <div
            v-for="term in recentSearches"
            :key="term"
            class="global-search__history-item"
            @click="useHistoryTerm(term)"
          >
            <el-icon><Timer /></el-icon>
            <span>{{ term }}</span>
            <el-icon
              class="global-search__history-remove"
              @click.stop="removeFromHistory(term)"
            >
              <Close />
            </el-icon>
          </div>
        </template>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Timer, Close } from '@element-plus/icons-vue'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import { useGlobalSearch } from '@/composables/useGlobalSearch'

const { t } = useI18n()
const router = useRouter()

const {
  searchResults,
  isSearching,
  hasResults,
  recentSearches,
  debouncedSearch,
  clearResults,
  clearHistory,
  removeFromHistory,
} = useGlobalSearch()

const inputRef = ref<any>(null)
const containerRef = ref<HTMLElement | null>(null)
const keyword = ref('')
const isFocused = ref(false)

// Active item tracking for keyboard nav
const activeGroupCode = ref('')
const activeMatchIdx = ref(-1)

const showDropdown = computed(() => {
  return isFocused.value && (
    keyword.value.trim().length >= 2 ||
    recentSearches.value.length > 0 ||
    isSearching.value
  )
})

// Build flat list of navigable items for keyboard
const flatItems = computed(() => {
  const items: { objectCode: string; recordId: string; idx: number }[] = []
  for (const group of searchResults.value) {
    group.matches.forEach((m, i) => {
      items.push({ objectCode: group.object_code, recordId: m.record_id, idx: i })
    })
  }
  return items
})

const isItemActive = (groupCode: string, matchIdx: number) => {
  return activeGroupCode.value === groupCode && activeMatchIdx.value === matchIdx
}

const setActiveItem = (groupCode: string, matchIdx: number) => {
  activeGroupCode.value = groupCode
  activeMatchIdx.value = matchIdx
}

const handleFocus = () => {
  isFocused.value = true
}

const handleBlur = () => {
  // Delay to allow click events on dropdown items
  setTimeout(() => {
    isFocused.value = false
  }, 200)
}

const handleInput = (val: string) => {
  if (val.trim().length >= 2) {
    debouncedSearch(val)
  } else {
    clearResults()
  }
  activeGroupCode.value = ''
  activeMatchIdx.value = -1
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    isFocused.value = false
    ;(inputRef.value as any)?.$el?.querySelector('input')?.blur()
    return
  }

  if (!hasResults.value) return

  const items = flatItems.value
  if (items.length === 0) return

  // Find current flat index
  let currentFlatIdx = items.findIndex(
    (item) => item.objectCode === activeGroupCode.value && item.idx === activeMatchIdx.value
  )

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    currentFlatIdx = currentFlatIdx < items.length - 1 ? currentFlatIdx + 1 : 0
    const item = items[currentFlatIdx]
    setActiveItem(item.objectCode, item.idx)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    currentFlatIdx = currentFlatIdx > 0 ? currentFlatIdx - 1 : items.length - 1
    const item = items[currentFlatIdx]
    setActiveItem(item.objectCode, item.idx)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (currentFlatIdx >= 0 && currentFlatIdx < items.length) {
      const item = items[currentFlatIdx]
      navigateToRecord(item.objectCode, item.recordId)
    }
  }
}

const navigateToRecord = (objectCode: string, recordId: string) => {
  isFocused.value = false
  keyword.value = ''
  clearResults()
  router.push(`/objects/${encodeURIComponent(objectCode)}/${encodeURIComponent(recordId)}`)
}

const useHistoryTerm = (term: string) => {
  keyword.value = term
  debouncedSearch(term, 0)
}

// ── Global hotkey: Ctrl+K / ⌘+K ──────────────────────────────────
const handleGlobalKeydown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    nextTick(() => {
      const inputEl = (inputRef.value as any)?.$el?.querySelector('input')
      inputEl?.focus()
      inputEl?.select()
    })
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style scoped lang="scss">
.global-search {
  position: relative;
  width: 320px;
  max-width: 100%;
  transition: width 0.2s ease;

  &.is-focused {
    width: 420px;
  }
}

.global-search__input {
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    background-color: var(--el-fill-color-light);
    box-shadow: none;
    transition: all 0.2s ease;
  }

  :deep(.el-input__wrapper:hover) {
    background-color: var(--el-fill-color);
  }

  :deep(.el-input__wrapper.is-focus) {
    background-color: var(--el-bg-color);
    box-shadow: 0 0 0 1px var(--el-color-primary) inset;
  }
}

.global-search__dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  max-height: 420px;
  overflow-y: auto;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  box-shadow: var(--el-box-shadow-light);
  z-index: 2000;
  padding: 6px 0;
}

.global-search__loading {
  padding: 16px;
}

.global-search__group {
  &:not(:last-child) {
    border-bottom: 1px solid var(--el-border-color-extra-light);
    margin-bottom: 4px;
    padding-bottom: 4px;
  }
}

.global-search__group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.global-search__group-name {
  flex: 1;
}

.global-search__item {
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.1s;

  &:hover,
  &.is-active {
    background-color: var(--el-fill-color-light);
  }
}

.global-search__item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  line-height: 1.4;
}

.global-search__item-match {
  display: flex;
  gap: 6px;
  margin-top: 2px;
  font-size: 12px;
}

.global-search__item-field {
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.global-search__item-value {
  color: var(--el-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-search__empty {
  padding: 24px 16px;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.global-search__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 600;
}

.global-search__history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition: background 0.1s;

  &:hover {
    background-color: var(--el-fill-color-light);
  }
}

.global-search__history-remove {
  margin-left: auto;
  color: var(--el-text-color-placeholder);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;

  .global-search__history-item:hover & {
    opacity: 1;
  }

  &:hover {
    color: var(--el-color-danger);
  }
}

// Dropdown transition
.search-dropdown-enter-active,
.search-dropdown-leave-active {
  transition: all 0.2s ease;
}

.search-dropdown-enter-from,
.search-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
