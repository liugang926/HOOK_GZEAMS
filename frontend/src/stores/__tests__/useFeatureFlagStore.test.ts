import { describe, expect, it, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFeatureFlagStore } from '../featureFlag'

// Mock the systemConfigApi
vi.mock('@/api/system', () => ({
    systemConfigApi: {
        getByCategory: vi.fn(),
    },
}))

import { systemConfigApi } from '@/api/system'
const mockGetByCategory = vi.mocked(systemConfigApi.getByCategory)

describe('useFeatureFlagStore', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
        vi.clearAllMocks()
    })

    it('starts with empty flags and isLoaded = false', () => {
        const store = useFeatureFlagStore()
        expect(store.flags).toEqual({})
        expect(store.isLoaded).toBe(false)
        expect(store.isLoading).toBe(false)
    })

    it('isEnabled returns false for unknown flags', () => {
        const store = useFeatureFlagStore()
        expect(store.isEnabled('runtime_i18n_enabled')).toBe(false)
        expect(store.isEnabled('nonexistent_flag')).toBe(false)
    })

    it('loads flags from API (results format)', async () => {
        mockGetByCategory.mockResolvedValue({
            results: [
                { configKey: 'runtime_i18n_enabled', configValue: 'true', valueType: 'boolean' },
                { configKey: 'field_code_strict_mode', configValue: 'false', valueType: 'boolean' },
            ],
        })

        const store = useFeatureFlagStore()
        await store.loadFlags()

        expect(store.isEnabled('runtime_i18n_enabled')).toBe(true)
        expect(store.isEnabled('field_code_strict_mode')).toBe(false)
        expect(store.isLoaded).toBe(true)
        expect(mockGetByCategory).toHaveBeenCalledWith('feature_flag', { page_size: 100 })
    })

    it('loads flags from API (array format)', async () => {
        mockGetByCategory.mockResolvedValue([
            { config_key: 'layout_merge_unified_enabled', config_value: 'true' },
        ])

        const store = useFeatureFlagStore()
        await store.loadFlags()

        expect(store.isEnabled('layout_merge_unified_enabled')).toBe(true)
        expect(store.isLoaded).toBe(true)
    })

    it('handles API errors gracefully', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { })
        mockGetByCategory.mockRejectedValue(new Error('Network error'))

        const store = useFeatureFlagStore()
        await store.loadFlags()

        expect(store.flags).toEqual({})
        expect(store.isLoaded).toBe(false)
        expect(store.isLoading).toBe(false)
        consoleSpy.mockRestore()
    })

    it('refreshFlags reloads from API', async () => {
        mockGetByCategory.mockResolvedValue({
            results: [
                { configKey: 'runtime_i18n_enabled', configValue: 'true' },
            ],
        })

        const store = useFeatureFlagStore()
        await store.loadFlags()
        expect(store.isEnabled('runtime_i18n_enabled')).toBe(true)

        // Admin changes the flag
        mockGetByCategory.mockResolvedValue({
            results: [
                { configKey: 'runtime_i18n_enabled', configValue: 'false' },
            ],
        })

        await store.refreshFlags()
        expect(store.isEnabled('runtime_i18n_enabled')).toBe(false)
        expect(mockGetByCategory).toHaveBeenCalledTimes(2)
    })

    it('treats "1" and "yes" as truthy', async () => {
        mockGetByCategory.mockResolvedValue({
            results: [
                { configKey: 'flag_one', configValue: '1' },
                { configKey: 'flag_yes', configValue: 'yes' },
                { configKey: 'flag_no', configValue: 'no' },
            ],
        })

        const store = useFeatureFlagStore()
        await store.loadFlags()

        expect(store.isEnabled('flag_one')).toBe(true)
        expect(store.isEnabled('flag_yes')).toBe(true)
        expect(store.isEnabled('flag_no')).toBe(false)
    })
})
