import { ref, computed } from 'vue'
import { dynamicApi } from '@/api/dynamic'
import type { GlobalSearchResult } from '@/api/dynamic'

const STORAGE_KEY = 'gzeams:search-history'
const MAX_HISTORY = 10

// Module-level state for sharing across components
const searchResults = ref<GlobalSearchResult[]>([])
const isSearching = ref(false)
const searchError = ref<string | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveHistory(history: string[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)))
  } catch {
    // localStorage unavailable
  }
}

/**
 * Composable for global cross-object search.
 * Manages search state, debounce, caching, and recent history.
 */
export function useGlobalSearch() {
  const recentSearches = ref<string[]>(loadHistory())

  const hasResults = computed(() => searchResults.value.length > 0)

  const totalMatchCount = computed(() =>
    searchResults.value.reduce((sum, group) => sum + group.matches.length, 0)
  )

  const search = async (keyword: string, options?: { limit?: number; objectCodes?: string[] }) => {
    const trimmed = (keyword || '').trim()
    if (trimmed.length < 2) {
      searchResults.value = []
      return
    }

    isSearching.value = true
    searchError.value = null

    try {
      const resp = await dynamicApi.globalSearch(trimmed, options)
      const data = (resp as any)?.data ?? resp
      searchResults.value = Array.isArray(data) ? data : []

      // Save to search history
      addToHistory(trimmed)
    } catch (err: any) {
      searchError.value = err?.message || 'Search failed'
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  const debouncedSearch = (
    keyword: string,
    delayMs = 300,
    options?: { limit?: number; objectCodes?: string[] }
  ) => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => search(keyword, options), delayMs)
  }

  const clearResults = () => {
    searchResults.value = []
    searchError.value = null
  }

  const addToHistory = (keyword: string) => {
    const filtered = recentSearches.value.filter(
      (k) => k.toLowerCase() !== keyword.toLowerCase()
    )
    filtered.unshift(keyword)
    recentSearches.value = filtered.slice(0, MAX_HISTORY)
    saveHistory(recentSearches.value)
  }

  const clearHistory = () => {
    recentSearches.value = []
    saveHistory([])
  }

  const removeFromHistory = (keyword: string) => {
    recentSearches.value = recentSearches.value.filter(
      (k) => k.toLowerCase() !== keyword.toLowerCase()
    )
    saveHistory(recentSearches.value)
  }

  return {
    // State
    searchResults,
    isSearching,
    searchError,
    recentSearches,
    hasResults,
    totalMatchCount,

    // Actions
    search,
    debouncedSearch,
    clearResults,
    clearHistory,
    removeFromHistory,
  }
}
