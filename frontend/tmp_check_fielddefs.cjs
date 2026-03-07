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
  await page.goto('http://127.0.0.1:5173/system/field-definitions?objectCode=Asset&objectName=Asset', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const rows = await page.locator('.el-table__body-wrapper tbody tr').evaluateAll((trs) => trs.map((tr) => Array.from(tr.querySelectorAll('td')).map(td => (td.textContent || '').trim())));
  const matched = rows.filter((cols) => cols.some(c => c === 'images' || c === 'attachments'));
  console.log(JSON.stringify({ url: page.url(), matched }, null, 2));
  await page.screenshot({ path: 'tmp-field-def-list-asset.png', fullPage: true });
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });
