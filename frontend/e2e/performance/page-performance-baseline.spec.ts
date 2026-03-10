import { test, expect, type Route } from '@playwright/test'

// =============================================================================
// Page Performance Baseline — Collects Web Vitals + custom TTI for key pages
//
// Metrics are attached as test attachments (JSON), which can be consumed by
// scripts/performance-baseline.mjs to produce history + trend reports.
// =============================================================================

const OBJECT_CODE = 'Asset'
const DETAIL_RECORD_ID = 'perf-baseline-001'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fulfillJson(route: Route, data: unknown, status = 200) {
    return route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(data),
    })
}

/** Inject a Performance‐API shim that collects LCP/FCP from PerformanceObserver */
async function injectPerfObserver(page: import('@playwright/test').Page) {
    await page.addInitScript(() => {
        // @ts-expect-error custom global
        window.__perfMetrics = { lcp: 0, fcp: 0 }

        // FCP — from paint entries
        const fcpObserver = new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                if (entry.name === 'first-contentful-paint') {
                    // @ts-expect-error custom global
                    window.__perfMetrics.fcp = entry.startTime
                }
            }
        })
        try {
            fcpObserver.observe({ type: 'paint', buffered: true })
        } catch { /* unsupported browser */ }

        // LCP
        const lcpObserver = new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries()
            if (entries.length) {
                // @ts-expect-error custom global
                window.__perfMetrics.lcp = entries[entries.length - 1].startTime
            }
        })
        try {
            lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true })
        } catch { /* unsupported browser */ }
    })
}

/** Read collected perf metrics from the page */
async function readPerfMetrics(page: import('@playwright/test').Page) {
    return page.evaluate(() => {
        // @ts-expect-error custom global
        const m = window.__perfMetrics || {}
        return {
            lcpMs: Math.round(Number(m.lcp) || 0),
            fcpMs: Math.round(Number(m.fcp) || 0),
        }
    })
}

// ---------------------------------------------------------------------------
// Shared API mock
// ---------------------------------------------------------------------------

function setupCommonMocks(page: import('@playwright/test').Page) {
    return page.route('**/*', async (route) => {
        const url = new URL(route.request().url())
        const pathname = url.pathname
        if (!pathname.startsWith('/api/')) return route.continue()

        // --- Auth / User ---
        if (pathname.endsWith('/api/system/objects/User/me/')) {
            return fulfillJson(route, {
                success: true,
                data: {
                    id: 'user-perf-baseline',
                    username: 'admin',
                    roles: ['admin'],
                    permissions: ['*'],
                    primaryOrganization: { id: 'org-perf', name: 'Perf Org', code: 'PERF' },
                },
            })
        }

        // --- Menu ---
        if (pathname.endsWith('/api/system/menu/')) {
            return fulfillJson(route, { groups: [], items: [] })
        }
        if (pathname.endsWith('/api/system/menu/flat/')) {
            return fulfillJson(route, { success: true, data: [] })
        }
        if (pathname.endsWith('/api/system/menu/config/')) {
            return fulfillJson(route, { schema: {}, common_groups: [], common_icons: [] })
        }

        // --- Feature flags ---
        if (pathname.endsWith('/api/system/configs/') && url.searchParams.get('category') === 'feature_flag') {
            return fulfillJson(route, { results: [], count: 0 })
        }

        // --- Business objects ---
        if (pathname.endsWith('/api/system/objects/')) {
            return fulfillJson(route, {
                success: true,
                data: {
                    results: [
                        { code: OBJECT_CODE, name: OBJECT_CODE, id: '1', isHardcoded: true },
                    ],
                    count: 1,
                },
            })
        }

        // --- Object metadata ---
        if (pathname.endsWith(`/api/system/objects/${OBJECT_CODE}/metadata/`)) {
            return fulfillJson(route, {
                success: true,
                data: {
                    code: OBJECT_CODE,
                    name: OBJECT_CODE,
                    permissions: { view: true, add: true, change: true, delete: true },
                },
            })
        }

        // --- Runtime (for detail/edit pages) ---
        if (pathname.match(/\/api\/system\/objects\/\w+\/runtime\//)) {
            return fulfillJson(route, {
                success: true,
                data: {
                    runtimeVersion: 1,
                    context: 'form',
                    fields: {
                        editableFields: [
                            { code: 'asset_code', name: 'Asset Code', label: 'Asset Code', fieldType: 'text', showInForm: true, sortOrder: 1 },
                            { code: 'asset_name', name: 'Asset Name', label: 'Asset Name', fieldType: 'text', showInForm: true, sortOrder: 2 },
                            { code: 'status', name: 'Status', label: 'Status', fieldType: 'text', showInForm: true, sortOrder: 3 },
                        ],
                        reverseRelations: [],
                    },
                    layout: {
                        layoutType: 'form',
                        layoutConfig: {
                            sections: [
                                {
                                    id: 'basic',
                                    name: 'basic',
                                    title: 'Basic',
                                    columns: 2,
                                    fields: [
                                        { fieldCode: 'asset_code', label: 'Asset Code', span: 12 },
                                        { fieldCode: 'asset_name', label: 'Asset Name', span: 12 },
                                        { fieldCode: 'status', label: 'Status', span: 12 },
                                    ],
                                },
                            ],
                        },
                    },
                    isDefault: true,
                },
            })
        }

        // --- List data ---
        if (pathname.match(/\/api\/system\/objects\/\w+\/data\//)) {
            const rows = Array.from({ length: 20 }, (_, i) => ({
                id: `row-${i}`,
                asset_code: `A-${String(i + 1).padStart(4, '0')}`,
                asset_name: `Test Asset ${i + 1}`,
                status: i % 2 === 0 ? 'active' : 'inactive',
            }))
            return fulfillJson(route, {
                success: true,
                data: { results: rows, count: 100 },
            })
        }

        // --- Detail record ---
        if (pathname.match(/\/api\/system\/objects\/\w+\/data\/[\w-]+\//)) {
            return fulfillJson(route, {
                success: true,
                data: {
                    id: DETAIL_RECORD_ID,
                    asset_code: 'A-0001',
                    asset_name: 'Test Asset 1',
                    status: 'active',
                },
            })
        }

        // Fallback
        return fulfillJson(route, { success: true, data: {} })
    })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe('Page Performance Baselines', () => {
    test.beforeEach(async ({ page }) => {
        await page.addInitScript(() => {
            localStorage.setItem('access_token', 'e2e-perf-baseline-token')
            localStorage.setItem('current_org_id', 'org-perf')
            localStorage.setItem('locale', 'en-US')
        })
        await injectPerfObserver(page)
        await setupCommonMocks(page)
    })

    test('Dashboard / Home page', async ({ page }, testInfo) => {
        const navStart = Date.now()
        await page.goto('/')
        // Wait for the main layout to be visible
        await expect(page.locator('.main-layout')).toBeVisible({ timeout: 15000 })
        const interactiveMs = Date.now() - navStart

        const vitals = await readPerfMetrics(page)

        await testInfo.attach('page-perf-metrics', {
            body: JSON.stringify({
                page: 'dashboard',
                route: '/',
                interactiveMs,
                ...vitals,
            }, null, 2),
            contentType: 'application/json',
        })

        expect(interactiveMs).toBeGreaterThan(0)
    })

    test('Object List page', async ({ page }, testInfo) => {
        const navStart = Date.now()
        await page.goto(`/objects/${OBJECT_CODE}`)
        // Wait for table rows to appear
        await expect(page.locator('.el-table__row').first()).toBeVisible({ timeout: 15000 })
        const interactiveMs = Date.now() - navStart

        const vitals = await readPerfMetrics(page)

        await testInfo.attach('page-perf-metrics', {
            body: JSON.stringify({
                page: 'list',
                route: `/objects/${OBJECT_CODE}`,
                interactiveMs,
                ...vitals,
            }, null, 2),
            contentType: 'application/json',
        })

        expect(interactiveMs).toBeGreaterThan(0)
    })

    test('Object Create page', async ({ page }, testInfo) => {
        const navStart = Date.now()
        await page.goto(`/objects/${OBJECT_CODE}/create`)
        // Wait for form to render
        await expect(page.locator('.dynamic-form-page, .base-detail-page, .el-form').first()).toBeVisible({ timeout: 15000 })
        const interactiveMs = Date.now() - navStart

        const vitals = await readPerfMetrics(page)

        await testInfo.attach('page-perf-metrics', {
            body: JSON.stringify({
                page: 'create',
                route: `/objects/${OBJECT_CODE}/create`,
                interactiveMs,
                ...vitals,
            }, null, 2),
            contentType: 'application/json',
        })

        expect(interactiveMs).toBeGreaterThan(0)
    })

    test('Object Detail page', async ({ page }, testInfo) => {
        const navStart = Date.now()
        await page.goto(`/objects/${OBJECT_CODE}/${DETAIL_RECORD_ID}`)
        // Wait for detail content
        await expect(
            page.locator('.base-detail-page, .dynamic-detail-page, .detail-header, .el-descriptions').first()
        ).toBeVisible({ timeout: 15000 })
        const interactiveMs = Date.now() - navStart

        const vitals = await readPerfMetrics(page)

        await testInfo.attach('page-perf-metrics', {
            body: JSON.stringify({
                page: 'detail',
                route: `/objects/${OBJECT_CODE}/${DETAIL_RECORD_ID}`,
                interactiveMs,
                ...vitals,
            }, null, 2),
            contentType: 'application/json',
        })

        expect(interactiveMs).toBeGreaterThan(0)
    })
})
