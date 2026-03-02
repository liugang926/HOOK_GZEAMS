import { test, expect } from '@playwright/test';

test.describe('Dynamic Object Routing Verification (with Login)', () => {
  const baseUrl = 'http://localhost:5174';

  async function login(page: any) {
    await page.goto(`${baseUrl}/login`);
    await page.waitForLoadState('domcontentloaded');

    try {
      // Fill login form - use placeholder text as selector
      const usernameInput = page.locator('input[placeholder="用户名"]').first();
      const passwordInput = page.locator('input[placeholder="密码"]').first();
      const loginButton = page.locator('button:has-text("登录")').first();

      await usernameInput.fill('admin');
      await passwordInput.fill('admin123');
      await loginButton.click();

      // Wait for navigation to dashboard or timeout
      await page.waitForURL(/\/dashboard/, { timeout: 8000 }).catch(() => {
        console.log('Login did not redirect to dashboard within timeout');
      });

      await page.waitForTimeout(1000);
    } catch (e) {
      console.log('Login attempt result:', e);
    }
  }

  test('1. Login and verify old TransferList route', async ({ page }) => {
    await login(page);
    await page.goto(`${baseUrl}/assets/operations/transfer`);
    await page.waitForLoadState('networkidle');

    const content = await page.content();
    const isLoginPage = content.includes('登录') || content.includes('Login');

    console.log('Old route /assets/operations/transfer:');
    console.log('  - Is on login page:', isLoginPage);
    console.log('  - Has 调拨单:', content.includes('调拨单'));
    console.log('  - Content length:', content.length);

    await page.screenshot({ path: 'screenshots/verify_old_transfer_route.png' });
  });

  test('2. Login and verify new dynamic AssetTransfer route', async ({ page }) => {
    await login(page);
    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle');

    const content = await page.content();
    const isLoginPage = content.includes('登录') || content.includes('Login');

    console.log('New route /objects/AssetTransfer:');
    console.log('  - Is on login page:', isLoginPage);
    console.log('  - Has transfer elements:', content.includes('调拨单') || content.includes('AssetTransfer'));
    console.log('  - Content length:', content.length);

    await page.screenshot({ path: 'screenshots/verify_dynamic_transfer_route.png' });
  });

  test('3. Compare old and new routes', async ({ page }) => {
    await login(page);

    // Visit old route
    await page.goto(`${baseUrl}/assets/operations/transfer`);
    await page.waitForLoadState('networkidle');
    const oldContent = await page.content();

    // Visit new route
    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle');
    const newContent = await page.content();

    console.log('Route comparison:');
    console.log('  - Old route content length:', oldContent.length);
    console.log('  - New route content length:', newContent.length);
    console.log('  - Are they the same:', oldContent.length === newContent.length);

    await page.screenshot({ path: 'screenshots/verify_route_comparison.png', fullPage: true });
  });

  test('4. Test multiple dynamic routes', async ({ page }) => {
    await login(page);

    const routes = [
      { code: 'AssetPickup', name: '领用单' },
      { code: 'AssetLoan', name: '借用单' },
      { code: 'AssetReturn', name: '归还单' },
      { code: 'Consumable', name: '耗材' }
    ];

    for (const route of routes) {
      await page.goto(`${baseUrl}/objects/${route.code}`);
      await page.waitForLoadState('networkidle');
      const content = await page.content();
      const isLoginPage = content.includes('登录');

      console.log(`${route.code} (${route.name}):`, isLoginPage ? 'Login redirect' : 'Accessible');
    }
  });
});
