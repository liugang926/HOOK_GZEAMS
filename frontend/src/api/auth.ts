/**
 * Authentication API Service
 */

import request from '@/utils/request'
import type { LoginData, LoginResponse } from '@/types/auth'

export const authApi = {
    /**
     * Login
     */
    login(data: LoginData): Promise<LoginResponse> {
        return request.post('/auth/login/', data)
    },

    /**
     * Logout
     */
    logout(): Promise<void> {
        return request.post('/auth/logout/')
    },

    /**
     * Refresh Token
     */
    refreshToken(token: string): Promise<{ token: string }> {
        return request.post('/auth/refresh/', { token })
    }
}
