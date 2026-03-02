import { test, expect } from '@playwright/test';

test.describe('Full Migration Verification', () => {
  const baseUrl = 'http://localhost:5174';

  async function login(page: any) {
    await page.goto(`${baseUrl}/login`);
    await page.waitForLoadState('domcontentloaded');

    const usernameInput = page.locator('input[placeholder="用户名"]').first();
    const passwordInput = page.locator('input[placeholder="密码"]').first();
    const loginButton = page.locator('button:has-text("登录")').first();

    await usernameInput.fill('admin');
    await passwordInput.fill('admin123');
    await loginButton.click();

    await page.waitForURL(/\/dashboard/, { timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(1000);
  }

  test('1. Capture network calls for old transfer route', async ({ page }) => {
    const apiCalls: string[] = [];

    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/') && !url.includes('src')) {
        apiCalls.push({
          url: url,
          method: request.method()
        });
      }
    });

    await login(page);
    apiCalls.length = 0; // Clear login calls

    await page.goto(`${baseUrl}/assets/operations/transfer`);
    await page.waitForLoadState('networkidle');

    console.log('=== Old Transfer Route API Calls ===');
    apiCalls.forEach(call => console.log(`  ${call.method} ${call.url}`));

    // Check which endpoint was used
    const usesOldEndpoint = apiCalls.some(c => c.url.includes('/assets/transfers/'));
    const usesDynamicEndpoint = apiCalls.some(c => c.url.includes('/api/system/objects/AssetTransfer') || c.url.includes('/api/objects/AssetTransfer'));

    console.log(`Uses old endpoint (/assets/transfers/): ${usesOldEndpoint}`);
    console.log(`Uses dynamic endpoint (/api/objects/): ${usesDynamicEndpoint}`);
  });

  test('2. Capture network calls for new dynamic route', async ({ page }) => {
    const apiCalls: any[] = [];

    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/') && !url.includes('src')) {
        apiCalls.push({
          url: url,
          method: request.method()
        });
      }
    });

    await login(page);
    apiCalls.length = 0; // Clear login calls

    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle');

    console.log('=== New Dynamic Route API Calls ===');
    apiCalls.forEach(call => console.log(`  ${call.method} ${call.url}`));

    const usesDynamicEndpoint = apiCalls.some(c => c.url.includes('/api/system/objects/AssetTransfer') || c.url.includes('/api/objects/AssetTransfer'));

    console.log(`Uses dynamic endpoint: ${usesDynamicEndpoint}`);
  });

  test('3. Check page content and components', async ({ page }) => {
    await login(page);

    // Check old route
    await page.goto(`${baseUrl}/assets/operations/transfer`);
    await page.waitForLoadState('networkidle');

    const oldPageContent = await page.content();
    const oldHasTransferText = oldPageContent.includes('调拨单');
    const oldHasTransferTable = oldPageContent.includes('transfer_no') || oldPageContent.includes('transferNo');
    const oldHasNewButton = oldPageContent.includes('新建调拨单');

    console.log('=== Old Route Content Analysis ===');
    console.log(`  Has "调拨单" text: ${oldHasTransferText}`);
    console.log(`  Has transfer table columns: ${oldHasTransferTable}`);
    console.log(`  Has "新建调拨单" button: ${oldHasNewButton}`);

    // Check new route
    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle');

    const newPageContent = await page.content();
    const newHasTransferText = newPageContent.includes('调拨单') || newPageContent.includes('AssetTransfer');
    const newHasDynamicComponent = newPageContent.includes('DynamicListPage') || newPageContent.includes('dynamic-list');
    const newHasBaseList = newPageContent.includes('BaseListPage') || newPageContent.includes('base-list');

    console.log('=== New Dynamic Route Content Analysis ===');
    console.log(`  Has transfer text: ${newHasTransferText}`);
    console.log(`  Has DynamicListPage component: ${newHasDynamicComponent}`);
    console.log(`  Has BaseListPage component: ${newHasBaseList}`);

    await page.screenshot({ path: 'screenshots/full_verify_dynamic_route.png', fullPage: true });
  });

  test('4. Verify API response format', async ({ page }) => {
    await login(page);

    // Make direct API call to check response format
    const token = await page.evaluate(async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token');
      return token;
    });

    console.log('Token from localStorage:', token ? 'Found' : 'Not found');

    if (token) {
      // Try calling dynamic API
      const response = await page.evaluate(async (t) => {
        try {
          const res = await fetch('http://localhost:8000/api/system/objects/AssetTransfer/', {
            headers: {
              'Authorization': `Bearer ${t}`,
              'Content-Type': 'application/json'
            }
          });
          const data = await res.json();
          return { status: res.status, data };
        } catch (e: any) {
          return { error: e.message };
        }
      }, token);

      console.log('=== Direct API Call Result ===');
      console.log(JSON.stringify(response, null, 2));
    }
  });

  test('5. Check console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await login(page);

    // Navigate to dynamic route
    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Wait for any async errors

    console.log('=== Console Errors ===');
    if (errors.length === 0) {
      console.log('  No console errors');
    } else {
      errors.forEach(e => console.log(`  ${e}`));
    }
  });

  test('6. Verify old route API calls', async ({ page }) => {
    const apiCalls: any[] = [];

    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/api/') && !url.includes('src')) {
        try {
          const contentType = response.headers()['content-type'] || '';
          let data = null;
          if (contentType.includes('application/json')) {
            data = await response.json().catch(() => null);
          }
          apiCalls.push({
            url: url,
            status: response.status(),
            data: data
          });
        } catch (e) {
          apiCalls.push({
            url: url,
            status: response.status(),
            error: String(e)
          });
        }
      }
    });

    await login(page);
    apiCalls.length = 0;

    await page.goto(`${baseUrl}/assets/operations/transfer`);
    await page.waitForLoadState('networkidle');

    console.log('=== Old Route - Detailed API Calls ===');
    apiCalls.forEach(call => {
      console.log(`  ${call.status} ${call.url}`);
      if (call.data && call.data.error) {
        console.log(`    Error: ${call.data.error.message || call.data.error.code}`);
      }
    });
  });

  test('7. Test all object routes accessibility', async ({ page }) => {
    await login(page);

    const objects = [
      'Asset',
      'AssetCategory',
      'AssetTransfer',
      'AssetPickup',
      'AssetLoan',
      'AssetReturn',
      'Supplier',
      'Location',
      'Consumable',
      'ConsumableCategory',
      'ConsumableStock',
      'PurchaseRequest',
      'Maintenance',
      'InventoryTask'
    ];

    console.log('=== Testing All Dynamic Routes ===');
    const results: any = {};

    for (const obj of objects) {
      await page.goto(`${baseUrl}/objects/${obj}`);
      await page.waitForLoadState('networkidle');

      const content = await page.content();
      const isLoginPage = content.includes('登录') && content.length < 400000;
      const hasError = content.includes('Error') || content.includes('404');

      results[obj] = {
        accessible: !isLoginPage && !hasError,
        isLogin: isLoginPage,
        hasError: hasError,
        contentLength: content.length
      };

      console.log(`  ${obj}: ${isLoginPage ? 'Login redirect' : hasError ? 'Error' : 'Accessible'} (${content.length} bytes)`);
    }
  });
});
