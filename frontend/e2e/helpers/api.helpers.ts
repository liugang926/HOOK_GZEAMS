/**
 * API Helper Functions for E2E Tests
 *
 * Provides utility functions for interacting with the backend API
 * during E2E tests. Useful for setup/teardown and data verification.
 */

const BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000/api'

/**
 * API response wrapper
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
}

/**
 * Login and return authentication token
 */
export async function apiLogin(username: string, password: string): Promise<string | null> {
  try {
    const response = await fetch(`${BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    const data: ApiResponse = await response.json()

    if (data.success && data.data?.token) {
      return data.data.token
    }

    return null
  } catch (error) {
    console.error('API login failed:', error)
    return null
  }
}

/**
 * Make authenticated API request
 */
export async function apiRequest<T = any>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  })

  return response.json()
}

/**
 * Create test asset
 */
export async function createTestAsset(token: string, assetData: any): Promise<any> {
  return apiRequest('/assets/', token, {
    method: 'POST',
    body: JSON.stringify(assetData)
  })
}

/**
 * Delete test asset by ID
 */
export async function deleteTestAsset(token: string, assetId: string): Promise<void> {
  await apiRequest(`/assets/${assetId}/`, token, {
    method: 'DELETE'
  })
}

/**
 * Get test user token (for setup/teardown)
 */
let cachedToken: string | null = null

export async function getTestUserToken(): Promise<string> {
  if (cachedToken) return cachedToken

  const username = process.env.E2E_USERNAME || 'admin'
  const password = process.env.E2E_PASSWORD || 'admin123'

  cachedToken = await apiLogin(username, password)
  return cachedToken || ''
}

/**
 * Clear cached token
 */
export function clearAuthToken(): void {
  cachedToken = null
}

/**
 * Setup test data - create a test asset category
 */
export async function setupTestCategory(token: string): Promise<any> {
  const timestamp = Date.now()
  const categoryData = {
    name: `E2E Test Category ${timestamp}`,
    code: `E2E_CAT_${timestamp}`,
    description: 'Category for E2E testing',
    is_active: true
  }

  return apiRequest('/assets/categories/', token, {
    method: 'POST',
    body: JSON.stringify(categoryData)
  })
}

/**
 * Cleanup test data
 */
export async function cleanupTestCategory(token: string, categoryId: string): Promise<void> {
  await apiRequest(`/assets/categories/${categoryId}/`, token, {
    method: 'DELETE'
  })
}
