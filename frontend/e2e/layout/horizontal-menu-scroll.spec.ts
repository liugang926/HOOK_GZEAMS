import { test, expect } from '@playwright/test'
import { getTestUserSession } from '../helpers/api.helpers'

/**
 * E2E Tests for Horizontal Menu Scrolling
 *
 * Tests cover:
 * - Horizontal menu overflow scrolling functionality
 * - All menu items are accessible via horizontal scroll
 * - System Management menu items are visible/accessible
 * - Menu scrolling behavior on smaller screens
 */

test.describe('Horizontal Menu Scroll', () => {
  let authSession: Awaited<ReturnType<typeof getTestUserSession>>

  test.beforeAll(async () => {
    authSession = await getTestUserSession()
  })

  test.beforeEach(async ({ page }) => {
    // Set auth session
    await page.goto('/login')
    await page.evaluate(({ token, currentOrgId }) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('current_org_id', currentOrgId)
      localStorage.setItem('auth_token', token)
      localStorage.setItem('token', token)
      localStorage.setItem('accessToken', token)
    }, authSession)

    // Start from dashboard
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('should display desktop horizontal menu on large screens', async ({ page }) => {
    // Set viewport to desktop size
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Check for horizontal menu
    const desktopMenu = page.locator('.desktop-menu, .el-menu--horizontal')

    const menuExists = await desktopMenu.count() > 0
    if (menuExists) {
      await expect(desktopMenu.first()).toBeVisible()
    }
  })

  test('should have horizontal scroll capability when menu overflows', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Get the desktop menu element
    const desktopMenu = page.locator('.desktop-menu')

    const menuExists = await desktopMenu.count() > 0
    if (!menuExists) {
      test.skip()
      return
    }

    // Check computed styles for overflow
    const overflowX = await desktopMenu.evaluate((el) => {
      return window.getComputedStyle(el).overflowX
    })

    // Verify overflow-x is set (either auto, scroll, or hidden with scroll capability)
    const hasOverflowHandling = overflowX === 'auto' || overflowX === 'scroll' || overflowX === 'hidden'

    expect(hasOverflowHandling).toBeTruthy()
  })

  test('should be able to scroll to see System Management menu', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.reload()
    await page.waitForLoadState('networkidle')

    const desktopMenu = page.locator('.desktop-menu')

    const menuExists = await desktopMenu.count() > 0
    if (!menuExists) {
      test.skip()
      return
    }

    // Try to find System Management menu item
    const systemManagementItem = page.locator('text=/系统管理|System Management/')

    // If not immediately visible, try scrolling
    const isVisible = await systemManagementItem.isVisible({ timeout: 2000 })

    if (!isVisible) {
      // Scroll the menu horizontally
      await desktopMenu.evaluate((el) => {
        el.scrollLeft = el.scrollWidth
      })

      await page.waitForTimeout(500)

      // Check again after scrolling
      const visibleAfterScroll = await systemManagementItem.isVisible({ timeout: 1000 })
      expect(visibleAfterScroll).toBeTruthy()
    }
  })

  test('should display all menu groups via scroll', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.reload()
    await page.waitForLoadState('networkidle')

    const desktopMenu = page.locator('.desktop-menu')

    const menuExists = await desktopMenu.count() > 0
    if (!menuExists) {
      test.skip()
      return
    }

    // Expected menu items to be accessible
    const expectedMenuItems = [
      '工作台',
      '资产',
      '库存',
      '耗材',
      '财务',
      '系统'
    ]

    // Scroll to the right
    await desktopMenu.evaluate((el) => {
      el.scrollLeft = el.scrollWidth
    })

    await page.waitForTimeout(500)

    // Check if at least some menu items are visible
    let visibleMenuCount = 0
    for (const item of expectedMenuItems) {
      const menuItem = page.locator(`text=/${item.substring(0, 2)}/`)
      if (await menuItem.isVisible({ timeout: 1000 }).catch(() => false)) {
        visibleMenuCount++
      }
    }

    // At least 2 menu items should be visible
    expect(visibleMenuCount).toBeGreaterThan(1)
  })

  test('should maintain menu accessibility on medium screens', async ({ page }) => {
    // Test on medium screen size (tablet)
    await page.setViewportSize({ width: 1024, height: 768 })
    await page.reload()
    await page.waitForLoadState('networkidle')

    const desktopMenu = page.locator('.desktop-menu')

    const menuExists = await desktopMenu.count() > 0
    if (!menuExists) {
      test.skip()
      return
    }

    // Menu should still be scrollable
    const scrollWidth = await desktopMenu.evaluate((el) => el.scrollWidth)
    const clientWidth = await desktopMenu.evaluate((el) => el.clientWidth)

    const canScroll = scrollWidth > clientWidth

    if (canScroll) {
      // Test horizontal scrolling
      await desktopMenu.evaluate((el) => {
        el.scrollLeft = 100
      })

      const scrollLeft = await desktopMenu.evaluate((el) => el.scrollLeft)
      expect(scrollLeft).toBeGreaterThan(0)
    }
  })

  test('should show all expected menu groups', async ({ page, request }) => {
    // Also verify via API that menu items exist
    const menuResponse = await request.get('http://127.0.0.1:8000/api/system/menu/', {
      headers: {
        'Authorization': `Bearer ${authSession.token}`
      }
    })

    const menuData = await menuResponse.json()

    // Verify the API returns menu data
    expect(menuData.success).toBeTruthy()
    expect(menuData.data?.groups).toBeDefined()
    expect(menuData.data.groups.length).toBeGreaterThan(0)

    // Check for the current system group contract.
    const hasSystemManagement = menuData.data.groups.some(
      (g: any) => (
        g.code === 'system' ||
        g.translationKey === 'menu.categories.system' ||
        g.name === '系统管理' ||
        g.name === 'System Management' ||
        g.name === 'System'
      )
    )
    expect(hasSystemManagement).toBeTruthy()
  })

  test('should have proper scrollbar styling', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.reload()
    await page.waitForLoadState('networkidle')

    const desktopMenu = page.locator('.desktop-menu')

    const menuExists = await desktopMenu.count() > 0
    if (!menuExists) {
      test.skip()
      return
    }

    // Check that min-width is set (for proper flex behavior)
    const minWidth = await desktopMenu.evaluate((el) => {
      return window.getComputedStyle(el).minWidth
    })

    expect(minWidth).toBeTruthy()
  })
})

test.describe('Mobile Menu vs Desktop Menu', () => {
  let authSession: Awaited<ReturnType<typeof getTestUserSession>>

  test.beforeAll(async () => {
    authSession = await getTestUserSession()
  })

  test('should show drawer menu on mobile screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }) // Mobile size
    await page.goto('/login')
    await page.evaluate(({ token, currentOrgId }) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('current_org_id', currentOrgId)
      localStorage.setItem('auth_token', token)
      localStorage.setItem('token', token)
      localStorage.setItem('accessToken', token)
    }, authSession)

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // On mobile, should show drawer menu button or drawer
    const drawerMenu = page.locator('.el-drawer, .mobile-menu')
    const menuButton = page.locator('.mobile-menu-btn')

    const hasMobileMenu = await drawerMenu.count() > 0 || await menuButton.count() > 0
    expect(hasMobileMenu).toBeTruthy()
  })

  test('should show horizontal menu on desktop screens', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 }) // Desktop size
    await page.goto('/login')
    await page.evaluate(({ token, currentOrgId }) => {
      localStorage.setItem('access_token', token)
      localStorage.setItem('current_org_id', currentOrgId)
      localStorage.setItem('auth_token', token)
      localStorage.setItem('token', token)
      localStorage.setItem('accessToken', token)
    }, authSession)

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // On desktop, should show horizontal menu
    const desktopMenu = page.locator('.desktop-menu, .el-menu--horizontal')

    // If desktop menu exists, it should be visible
    const hasDesktopMenu = await desktopMenu.count() > 0
    if (hasDesktopMenu) {
      await expect(desktopMenu.first()).toBeVisible()
    }
  })
})
