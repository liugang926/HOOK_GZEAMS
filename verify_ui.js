const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ['--start-maximized']
  });

  const page = await browser.newPage();

  // Navigate to the app
  await page.goto('http://localhost:5173');

  // Wait for page load
  await new Promise(r => setTimeout(r, 3000));

  // Check if we need to login
  const url = page.url();
  console.log('Current URL:', url);

  if (url.includes('login')) {
    console.log('Need to login first...');
    // Take screenshot of login page
    await page.screenshot({ path: 'login_page.png' });
  } else {
    // Navigate to business objects page
    console.log('Navigating to business objects...');
    await page.goto('http://localhost:5173/#/system/business-objects');
    await new Promise(r => setTimeout(r, 3000));

    // Click on Asset business object
    console.log('Looking for Asset in the list...');
    await page.screenshot({ path: 'business_objects_list.png' });

    // Try to find and click on Asset
    try {
      await page.waitForSelector('text/Asset', { timeout: 5000 });
      console.log('Found Asset!');
      await page.click('text/Asset');
      await new Promise(r => setTimeout(r, 2000));
      await page.screenshot({ path: 'asset_detail.png' });
    } catch (e) {
      console.log('Could not find Asset text:', e.message);
      await page.screenshot({ path: 'asset_not_found.png' });
    }
  }

  await browser.close();
})();
