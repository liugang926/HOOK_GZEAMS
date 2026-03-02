import { test, expect } from '@playwright/test';

test('Check login page selectors', async ({ page }) => {
  await page.goto('http://localhost:5175/login');

  // Take screenshot of login page
  await page.screenshot({
    path: 'test-results/login-page.png',
    fullPage: true
  });

  // Wait and inspect
  await page.waitForTimeout(3000);

  console.log('Login page loaded');
  console.log('URL:', page.url());
  console.log('Title:', await page.title());

  // Try to find any input fields
  const inputs = await page.locator('input').all();
  console.log(`Found ${inputs.length} input elements`);

  for (let i = 0; i < Math.min(inputs.length, 5); i++) {
    const input = inputs[i];
    const placeholder = await input.getAttribute('placeholder');
    const name = await input.getAttribute('name');
    const type = await input.getAttribute('type');
    console.log(`Input ${i}: name=${name}, type=${type}, placeholder=${placeholder}`);
  }

  // Try to find any buttons
  const buttons = await page.locator('button').all();
  console.log(`Found ${buttons.length} button elements`);

  for (let i = 0; i < Math.min(buttons.length, 3); i++) {
    const button = buttons[i];
    const text = await button.textContent();
    const type = await button.getAttribute('type');
    console.log(`Button ${i}: type=${type}, text=${text?.trim()}`);
  }
});
