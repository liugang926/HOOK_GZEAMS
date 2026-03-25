import type { Page, Route } from '@playwright/test'
import {
  LOOKUP_USER_POOL,
  pickLookupUsersBySearch,
  type LookupBatchGetRequest,
  type LookupTraceWindow,
  type LookupUserRecord
} from './reference-lookup.fixtures'

export interface ReferenceLookupCurrentUser {
  id: string
  username?: string
  roles?: string[]
  permissions?: string[]
  primaryOrganization?: {
    id: string
    name: string
    code: string
  }
}

export interface ReferenceLookupRouteContext {
  route: Route
  url: URL
  pathname: string
}

export interface ReferenceLookupApiOptions {
  accessToken: string
  orgId: string
  locale?: string
  currentUser: ReferenceLookupCurrentUser
  localStorageEntries?: Record<string, string>
  trackLookupGetKeys?: boolean
  searchKeys?: Array<keyof LookupUserRecord>
  handleApiRoute?: (context: ReferenceLookupRouteContext) => Promise<boolean> | boolean
}

export function fulfillSuccess(route: Route, data: unknown) {
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, data })
  })
}

export async function mockReferenceLookupApis(
  page: Page,
  options: ReferenceLookupApiOptions
): Promise<void> {
  await page.addInitScript((init) => {
    const {
      accessToken,
      orgId,
      locale,
      localStorageEntries,
      trackLookupGetKeys
    } = init

    if (trackLookupGetKeys) {
      const lookupWindow = window as LookupTraceWindow
      lookupWindow.__lookupGetKeys = []
      const originalGetItem = localStorage.getItem.bind(localStorage)
      localStorage.getItem = ((key: string) => {
        lookupWindow.__lookupGetKeys?.push(String(key || ''))
        return originalGetItem(key)
      }) as Storage['getItem']
    }

    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('current_org_id', orgId)
    localStorage.setItem('locale', locale)

    for (const [key, value] of Object.entries(localStorageEntries || {})) {
      localStorage.setItem(key, value)
    }
  }, {
    accessToken: options.accessToken,
    orgId: options.orgId,
    locale: options.locale || 'en-US',
    localStorageEntries: options.localStorageEntries || {},
    trackLookupGetKeys: options.trackLookupGetKeys === true
  })

  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url())
    const pathname = url.pathname

    if (!pathname.startsWith('/api/')) return route.continue()

    if (options.handleApiRoute && await options.handleApiRoute({ route, url, pathname })) {
      return
    }

    if (pathname.endsWith('/api/system/objects/User/me/')) {
      return fulfillSuccess(route, {
        id: options.currentUser.id,
        username: options.currentUser.username || 'admin',
        roles: options.currentUser.roles || ['admin'],
        permissions: options.currentUser.permissions || ['*'],
        primaryOrganization: options.currentUser.primaryOrganization || {
          id: options.orgId,
          name: 'Reference Lookup Org',
          code: 'LOOKUP'
        }
      })
    }

    if (pathname.endsWith('/api/system/menu/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ groups: [], items: [] })
      })
    }

    if (pathname.endsWith('/api/system/menu/flat/')) {
      return fulfillSuccess(route, [])
    }

    if (pathname.endsWith('/api/system/menu/config/')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ schema: {}, common_groups: [], common_icons: [] })
      })
    }

    if (pathname.endsWith('/api/system/objects/User/batch-get/')) {
      const body = route.request().postDataJSON() as LookupBatchGetRequest
      const ids = Array.isArray(body?.ids) ? body.ids.map((id) => String(id)) : []
      const map = new Map(LOOKUP_USER_POOL.map((user) => [String(user.id), user]))
      const results = ids
        .map((id) => map.get(id))
        .filter((item): item is LookupUserRecord => !!item)
      const missing_ids = ids.filter((id) => !map.has(id))
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, results, missing_ids })
      })
    }

    if (/\/api\/system\/objects\/User\/[^/]+\/$/.test(pathname)) {
      const id = pathname.split('/').filter(Boolean).pop() || ''
      const user = LOOKUP_USER_POOL.find((item) => item.id === id)
      if (!user) {
        return route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ success: false, message: 'not found' })
        })
      }
      return fulfillSuccess(route, user)
    }

    if (pathname.endsWith('/api/system/objects/User/')) {
      const search = url.searchParams.get('search') || ''
      const pageNo = Number(url.searchParams.get('page') || '1')
      const pageSize = Number(url.searchParams.get('page_size') || '20')
      const filtered = pickLookupUsersBySearch(search, options.searchKeys || ['fullName', 'username', 'code'])
      const start = Math.max(0, (pageNo - 1) * pageSize)
      const results = filtered.slice(start, start + pageSize)
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          count: filtered.length,
          results
        })
      })
    }

    return fulfillSuccess(route, {})
  })
}
