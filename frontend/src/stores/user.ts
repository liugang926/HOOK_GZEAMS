import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import { userApi } from '@/api/users'
import { useLocaleStore } from '@/stores/locale'
import { normalizeLocale } from '@/locales'
import { getStoredLocaleSource, setStoredLocaleSource } from '@/platform/i18n/localePreference'
import {
    clearStoredAccessToken,
    clearStoredCurrentOrgId,
    getStoredAccessToken,
    setStoredAccessToken,
    setStoredCurrentOrgId
} from '@/platform/auth/sessionPreference'
import type { LoginData } from '@/types/auth'
import type { User } from '@/types/common'

type CurrentOrganization = {
    id: string
    name: string
    role?: string
    code?: string
}

export const useUserStore = defineStore('user', () => {
    const token = ref(getStoredAccessToken())
    const userInfo = ref<User | null>(null)
    const currentOrganization = ref<CurrentOrganization | null>(null)
    const roles = ref<string[]>([])
    const permissions = ref<string[]>([])

    const applyProfileLocale = (user: User | null) => {
        const preferredLanguage = user?.preferredLanguage
        if (!preferredLanguage) return

        const localeSource = getStoredLocaleSource()
        if (localeSource === 'local') return

        const localeStore = useLocaleStore()
        const targetLocale = normalizeLocale(preferredLanguage)

        if (localeStore.currentLocale !== targetLocale) {
            localeStore.setLocale(targetLocale)
        }
        setStoredLocaleSource('profile')
    }

    const login = async (loginForm: LoginData) => {
        try {
            const res = await authApi.login(loginForm)
            if (res.token) {
                token.value = res.token
                setStoredAccessToken(res.token)

                // Save organization ID for subsequent requests
                if (res.organization) {
                    currentOrganization.value = res.organization
                    setStoredCurrentOrgId(res.organization.id)
                }

                await getUserInfo()
                return Promise.resolve()
            }
            return Promise.reject(new Error('Token not found'))
        } catch (error) {
            return Promise.reject(error)
        }
    }

    const getUserInfo = async () => {
        try {
            const user = await userApi.getMe()
            userInfo.value = user
            applyProfileLocale(user)

            // Update organization from user info if available
            if (user.primaryOrganization) {
                currentOrganization.value = user.primaryOrganization
                setStoredCurrentOrgId(user.primaryOrganization.id)
            }

            // Assuming roles/permissions come from user object or separate API
            // Adapting based on standard response structure
            roles.value = user.roles || ['user']
            permissions.value = user.permissions || []
        } catch (error) {
            console.error('Get user info failed:', error)
            throw error
        }
    }

    const logout = () => {
        token.value = ''
        userInfo.value = null
        currentOrganization.value = null
        roles.value = []
        permissions.value = []
        clearStoredAccessToken()
        clearStoredCurrentOrgId()
    }

    return {
        token,
        userInfo,
        currentOrganization,
        roles,
        permissions,
        login,
        getUserInfo,
        logout
    }
})

