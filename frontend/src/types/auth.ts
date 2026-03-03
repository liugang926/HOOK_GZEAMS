/**
 * Auth Type Definitions
 */
import type { User } from '@/types/common'

export interface LoginData {
    username?: string
    password?: string
    code?: string
    uuid?: string
}

export interface LoginOrganization {
    id: string
    name: string
    role?: string
}

export interface LoginResponse {
    token: string
    refresh_token?: string
    expire?: number
    user?: User
    organization?: LoginOrganization | null
}
