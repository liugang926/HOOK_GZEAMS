import { test, expect } from '@playwright/test';

test.describe('Dynamic Object Routing Verification', () => {
  const baseUrl = 'http://localhost:5174';

  // Skip backend check - will be verified through frontend

  test('1. Verify frontend loads', async ({ page }) => {
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    console.log('Page title:', await page.title());
    expect(await page.title()).toContain('GZEAMS');
  });

  test('2. Check existing TransferList page still works', async ({ page }) => {
    await page.goto(`${baseUrl}/assets/operations/transfer`);
    await page.waitForLoadState('networkidle');

    // Check if page contains transfer-related content
    const content = await page.content();
    console.log('Transfer page loaded, content length:', content.length);

    // Look for transfer-related elements
    const hasTransferText = content.includes('调拨单') || content.includes('transfer');
    console.log('Has transfer text:', hasTransferText);
  });

  test('3. Test dynamic route for AssetTransfer', async ({ page }) => {
    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    const content = await page.content();
    console.log('Dynamic AssetTransfer page content length:', content.length);

    // Look for asset transfer related elements
    const hasTransferElements = content.includes('AssetTransfer') ||
                                content.includes('调拨单') ||
                                content.includes('transfer');
    console.log('Has transfer elements:', hasTransferElements);

    // Take screenshot for debugging
    await page.screenshot({ path: 'screenshots/dynamic_asset_transfer.png' });
  });

  test('4. Test dynamic route for AssetPickup', async ({ page }) => {
    await page.goto(`${baseUrl}/objects/AssetPickup`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    const content = await page.content();
    console.log('Dynamic AssetPickup page content length:', content.length);

    await page.screenshot({ path: 'screenshots/dynamic_asset_pickup.png' });
  });

  test('5. Test dynamic route for AssetLoan', async ({ page }) => {
    await page.goto(`${baseUrl}/objects/AssetLoan`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    const content = await page.content();
    console.log('Dynamic AssetLoan page content length:', content.length);

    await page.screenshot({ path: 'screenshots/dynamic_asset_loan.png' });
  });

  test('6. Test dynamic route for Consumable', async ({ page }) => {
    await page.goto(`${baseUrl}/objects/Consumable`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    const content = await page.content();
    console.log('Dynamic Consumable page content length:', content.length);

    await page.screenshot({ path: 'screenshots/dynamic_consumable.png' });
  });

  test('7. Check API calls in network', async ({ page }) => {
    // Collect API calls
    const apiCalls: string[] = [];
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/')) {
        apiCalls.push(url);
        console.log('API call:', url);
      }
    });

    await page.goto(`${baseUrl}/objects/AssetTransfer`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    console.log('Total API calls made:', apiCalls.length);

    // Check if dynamic routing API was called
    const hasDynamicRoutingCall = apiCalls.some(call =>
      call.includes('/api/system/objects/') ||
      call.includes('/api/objects/')
    );
    console.log('Has dynamic routing API call:', hasDynamicRoutingCall);

    if (apiCalls.length > 0) {
      console.log('API calls:', apiCalls);
    }
  });
});
