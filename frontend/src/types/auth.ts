/**
 * Auth Type Definitions
 */

export interface LoginData {
    username?: string
    password?: string
    code?: string
    uuid?: string
}

export interface LoginResponse {
    token: string
    refresh_token?: string
    expire?: number
}
