const { chromium } = require('@playwright/test');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ baseURL: 'http://127.0.0.1:5173' });
  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });
  const inputs = page.locator('.login-page .el-input__inner');
  await inputs.nth(0).fill('admin');
  await inputs.nth(1).fill('admin123');
  await page.locator('.login-page button.el-button--primary').click();
  await page.waitForURL(/\/dashboard$|\/$/, { timeout: 15000 });
  await page.goto('http://127.0.0.1:5173/objects/Asset/495b21b6-69fb-42ea-b8f6-05bf9bda4724/edit', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const fieldItems = await page.locator('.field-item').evaluateAll((nodes) => nodes.map((node) => ({
    text: node.textContent || '',
    html: node.innerHTML.slice(0, 300)
  })));
  const matched = fieldItems.filter((item) => /images|attachments/i.test(item.text));
  console.log(JSON.stringify({ url: page.url(), matched }, null, 2));
  await page.screenshot({ path: 'tmp-asset-edit-495b.png', fullPage: true });
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });
