import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import { userApi } from '@/api/users'

export const useUserStore = defineStore('user', () => {
    const token = ref(localStorage.getItem('access_token') || '')
    const userInfo = ref<any>(null)
    const currentOrganization = ref<any>(null)
    const roles = ref<string[]>([])
    const permissions = ref<string[]>([])

    const login = async (loginForm: any) => {
        try {
            const res = await authApi.login(loginForm)
            if (res.token) {
                token.value = res.token
                localStorage.setItem('access_token', res.token)

                // Save organization ID for subsequent requests
                if (res.organization) {
                    currentOrganization.value = res.organization
                    localStorage.setItem('current_org_id', res.organization.id)
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

            // Update organization from user info if available
            if (user.primaryOrganization) {
                currentOrganization.value = user.primaryOrganization
                localStorage.setItem('current_org_id', user.primaryOrganization.id)
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
        localStorage.removeItem('access_token')
        localStorage.removeItem('current_org_id')
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
