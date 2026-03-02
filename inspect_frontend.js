const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    const consoleMessages = [];
    const failedRequests = [];

    // Log console messages
    page.on('console', msg => {
        consoleMessages.push({
            type: msg.type(),
            text: msg.text()
        });
        if (msg.type() === 'error') {
            console.log('[CONSOLE ERROR]', msg.text());
        }
    });

    // Log failed requests
    page.on('response', response => {
        if (response.status() >= 400) {
            failedRequests.push({
                url: response.url(),
                status: response.status(),
                method: response.request().method()
            });
            console.log('[HTTP ' + response.status() + ']', response.request().method(), response.url());
        }
    });

    console.log('Navigating to http://localhost:5173 ...');

    try {
        await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 30000 });
        console.log('Page loaded!');

        // Take screenshot of homepage
        await page.screenshot({ path: 'C:/Users/ND/Desktop/Notting_Project/NEWSEAMS/test_screenshots/01_homepage.png', fullPage: true });
        console.log('Screenshot saved: test_screenshots/01_homepage.png');

        // Wait a bit more
        await page.waitForTimeout(3000);

        // Check if login form exists
        const hasPasswordInput = await page.$('input[type="password"]') !== null;
        console.log('Has password input:', hasPasswordInput);

        if (hasPasswordInput) {
            console.log('Attempting login...');

            // Try to find and fill username
            try {
                await page.fill('input[placeholder*="用户"], input[name="username"], input[type="text"]:first-child', 'admin', { timeout: 5000 });
                console.log('Filled username');
            } catch (e) {
                console.log('Username fill issue:', e.message);
            }

            // Fill password
            try {
                await page.fill('input[type="password"]', 'admin123');
                console.log('Filled password');
            } catch (e) {
                console.log('Password fill issue:', e.message);
            }

            // Click login button
            try {
                await page.click('button:has-text("登录"), button[type="submit"]', { timeout: 5000 });
                console.log('Clicked login button');
            } catch (e) {
                console.log('Login click issue:', e.message);
            }

            // Wait for navigation
            await page.waitForTimeout(5000);

            // Take screenshot after login
            await page.screenshot({ path: 'C:/Users/ND/Desktop/Notting_Project/NEWSEAMS/test_screenshots/02_after_login.png', fullPage: true });
            console.log('Screenshot saved: test_screenshots/02_after_login.png');

            // Get page title
            const title = await page.title();
            console.log('Page title after login:', title);

            // Get page content
            const bodyText = await page.evaluate(() => document.body.innerText);
            console.log('Page body text (first 300 chars):', bodyText.substring(0, 300));
        }

    } catch (e) {
        console.log('Error during navigation:', e.message);
        await page.screenshot({ path: 'C:/Users/ND/Desktop/Notting_Project/NEWSEAMS/test_screenshots/99_error.png', fullPage: true });
    }

    // Save logs
    const logs = {
        timestamp: new Date().toISOString(),
        consoleMessages: consoleMessages,
        failedRequests: failedRequests
    };

    fs.writeFileSync('C:/Users/ND/Desktop/Notting_Project/NEWSEAMS/test_screenshots/inspection_logs.json', JSON.stringify(logs, null, 2));
    console.log('Logs saved: test_screenshots/inspection_logs.json');

    console.log('Keeping browser open for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);

    await browser.close();
    console.log('Inspection complete!');
})();
