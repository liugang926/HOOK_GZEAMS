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
        return request.post('/auth/login/', data, { noAuth: true } as any)
    },

    /**
     * Logout
     */
    logout(): Promise<void> {
        return request.post('/auth/logout/', undefined, { noAuth: true } as any)
    },

    /**
     * Refresh Token
     */
    refreshToken(token: string): Promise<{ token: string }> {
        return request.post('/auth/refresh/', { token }, { noAuth: true } as any)
    }
}
