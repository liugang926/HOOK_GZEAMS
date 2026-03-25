import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { systemConfigApi } from '@/api/system'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Known feature flag keys. Extend as new flags are added. */
export type FeatureFlagKey =
    | 'runtime_i18n_enabled'
    | 'layout_merge_unified_enabled'
    | 'field_code_strict_mode'
    // Future Sprint flags (add here as they are created)
    | 'use_dynamic_menu'
    | 'enable_dual_mode_layout'
    | 'enable_swr_cache'
    | 'enable_activity_timeline'
    | (string & {}) // allow arbitrary string keys while preserving autocomplete

interface RawConfigItem {
    configKey?: string
    config_key?: string
    configValue?: string
    config_value?: string
    valueType?: string
    value_type?: string
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useFeatureFlagStore = defineStore('featureFlag', () => {
    // ----- State -----
    const flags = ref<Record<string, boolean>>({})
    const isLoaded = ref(false)
    const isLoading = ref(false)

    // ----- Getters -----
    /** All flag entries as a readonly record */
    const allFlags = computed(() => ({ ...flags.value }))

    // ----- Actions -----

    /**
     * Check if a feature flag is enabled.
     * Returns `false` for unknown flags (safe default).
     */
    function isEnabled(key: FeatureFlagKey): boolean {
        return flags.value[key] === true
    }

    /**
     * Load all feature flags from the backend.
     * Intended to be called once during app startup (e.g. from MainLayout onMounted).
     */
    async function loadFlags(): Promise<void> {
        if (isLoading.value) return
        isLoading.value = true

        try {
            const response = await systemConfigApi.getByCategory('feature_flag', {
                page_size: 100,
            })

            const items: RawConfigItem[] = Array.isArray(response)
                ? response
                : Array.isArray((response as Record<string, unknown>)?.results)
                    ? ((response as Record<string, unknown>).results as RawConfigItem[])
                    : []

            const parsed: Record<string, boolean> = {}
            for (const item of items) {
                const key = String(item.configKey || item.config_key || '').trim()
                const value = String(item.configValue || item.config_value || '').trim().toLowerCase()
                if (key) {
                    parsed[key] = value === 'true' || value === '1' || value === 'yes'
                }
            }

            flags.value = parsed
            isLoaded.value = true
        } catch (error) {
            console.error('[useFeatureFlagStore] failed to load feature flags', error)
            // Keep previous flags (or empty) — don't crash the app
        } finally {
            isLoading.value = false
        }
    }

    /**
     * Force-refresh flags from the backend.
     * Useful after an admin changes a flag in the SystemConfig UI.
     */
    async function refreshFlags(): Promise<void> {
        isLoaded.value = false
        return loadFlags()
    }

    return {
        // State
        flags,
        isLoaded,
        isLoading,
        // Getters
        allFlags,
        // Actions
        isEnabled,
        loadFlags,
        refreshFlags,
    }
})
