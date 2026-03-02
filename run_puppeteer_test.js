/**
 * Frontend Browser Automation Test using Puppeteer (Node.js)
 * Software Licenses Module Verification
 *
 * This test verifies the frontend software licenses module with real authentication.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Create screenshots directory
const SCREENSHOT_DIR = path.join(__dirname, 'test_screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function captureScreenshot(page, name) {
    const filePath = path.join(SCREENSHOT_DIR, `${name}.png`);
    return page.screenshot({ path: filePath, fullPage: true }).then(() => {
        console.log(`  [Screenshot] ${filePath}`);
        return filePath;
    });
}

// Debugging helper to get Vue app state
async function getVueAppState(page) {
    return await page.evaluate(() => {
        return {
            url: window.location.href,
            localStorage: {
                access_token: localStorage.getItem('access_token') || localStorage.getItem('token'),
                token: localStorage.getItem('token'),
                current_org_id: localStorage.getItem('current_org_id')
            },
            bodyText: document.body.innerText.substring(0, 500)
        };
    });
}

async function testFrontend() {
    const results = {
        tests: [],
        errors: [],
        screenshots: []
    };

    console.log('\n' + '='.repeat(70));
    console.log('BROWSER AUTOMATION TEST: SOFTWARE LICENSES MODULE (Puppeteer)');
    console.log('='.repeat(70));

    let browser;
    try {
        // Launch browser
        browser = await puppeteer.launch({
            headless: false,
            slowMo: 100,
            defaultViewport: { width: 1280, height: 720 },
            args: ['--disable-blink-features=AutomationControlled']
        });

        const page = await browser.newPage();

        // Enable console log capture
        const consoleMessages = [];
        page.on('console', msg => {
            const text = msg.text();
            consoleMessages.push({ type: msg.type(), text });
            if (msg.type() === 'error') {
                console.log(`  [Browser Console Error] ${text}`);
            }
        });

        // Track API calls
        const apiCalls = [];
        page.on('response', async response => {
            const url = response.url();
            if (url.includes('/api/') && !url.includes('.ts')) {
                const status = response.status();
                const method = response.request().method();
                apiCalls.push({ url, method, status });
                console.log(`  [API] ${method} ${url} -> ${status}`);
            }
        });

        // Test 1: Navigate to homepage
        console.log('\n[TEST 1] Navigate to frontend homepage');
        console.log('-'.repeat(70));
        await page.goto('http://localhost:5176', { waitUntil: 'networkidle2', timeout: 30000 });
        await new Promise(r => setTimeout(r, 2000));

        await captureScreenshot(page, '01_homepage');

        const appState = await getVueAppState(page);
        console.log(`  Page URL: ${appState.url}`);
        console.log(`  Has token: ${appState.localStorage.access_token || 'none'}`);
        results.tests.push({ name: 'Navigate to homepage', status: 'PASS' });

        // Test 2: Check if login is needed
        console.log('\n[TEST 2] Check login status');
        console.log('-'.repeat(70));

        const onLoginPage = appState.url.includes('/login');
        console.log(`  On login page: ${onLoginPage}`);

        if (onLoginPage && !appState.localStorage.access_token) {
            console.log('\n[TEST 3] Perform login via direct API (bypass proxy)');
            console.log('-'.repeat(70));

            // Direct API call to backend (bypassing Vite proxy)
            const loginResponse = await page.evaluate(async () => {
                try {
                    const response = await fetch('http://localhost:8000/api/auth/login/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: 'admin',
                            password: 'admin123'
                        })
                    });
                    const data = await response.json();
                    return { success: response.ok, status: response.status, data };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            });

            console.log(`  Login API response: ${loginResponse.status || 'error'}`);

            if (loginResponse.success && loginResponse.data && loginResponse.data.data && loginResponse.data.data.token) {
                // Store token in localStorage
                const token = loginResponse.data.data.token;
                await page.evaluate((token) => {
                    localStorage.setItem('access_token', token);
                    localStorage.setItem('token', token);
                }, token);
                console.log('  Token stored in localStorage');

                // Also store organization if available
                if (loginResponse.data.data.organization) {
                    await page.evaluate((orgId) => {
                        localStorage.setItem('current_org_id', orgId);
                    }, loginResponse.data.data.organization.id);
                }

                // Also store user info for the frontend
                if (loginResponse.data.data.user) {
                    await page.evaluate((user) => {
                        localStorage.setItem('user_info', JSON.stringify(user));
                    }, JSON.stringify(loginResponse.data.data.user));
                }

                console.log('  Login successful via direct API!');
                results.tests.push({ name: 'User login', status: 'PASS' });

                // Navigate to dashboard directly
                await page.goto('http://localhost:5176/dashboard', { waitUntil: 'networkidle2', timeout: 30000 });
                await new Promise(r => setTimeout(r, 2000));
            } else {
                console.log('  Login failed:', JSON.stringify(loginResponse));
                results.tests.push({ name: 'User login', status: 'FAIL', note: JSON.stringify(loginResponse) });
            }

            await captureScreenshot(page, '03_after_login');
        } else {
            console.log('  Already authenticated or not on login page');
            results.tests.push({ name: 'User login', status: 'SKIP', note: 'Already logged in' });
        }

        // Test 4: Navigate to Software Catalog
        console.log('\n[TEST 4] Navigate to Software Catalog page');
        console.log('-'.repeat(70));

        await page.goto('http://localhost:5176/software-licenses/software', { waitUntil: 'networkidle2', timeout: 30000 });
        await new Promise(r => setTimeout(r, 3000));

        const softwareState = await getVueAppState(page);
        console.log(`  URL: ${softwareState.url}`);
        await captureScreenshot(page, '04_software_catalog');

        const catalogBodyText = await page.evaluate(() => document.body.innerText);
        const catalogPageContent = await page.content();

        const hasSoftware = catalogPageContent.toLowerCase().includes('software') ||
                           catalogBodyText.includes('软件目录') ||
                           catalogBodyText.includes('Software Catalog') ||
                           catalogBodyText.includes('软件资产');
        const hasCreate = catalogBodyText.includes('新建') ||
                         catalogBodyText.includes('Create');

        console.log(`  Has software content: ${hasSoftware}`);
        console.log(`  Has create button: ${hasCreate}`);

        results.tests.push({
            name: 'Software Catalog page',
            status: hasSoftware ? 'PASS' : 'FAIL'
        });

        // Test 5: Navigate to Licenses page
        console.log('\n[TEST 5] Navigate to Licenses Management page');
        console.log('-'.repeat(70));

        await page.goto('http://localhost:5176/software-licenses/licenses', { waitUntil: 'networkidle2', timeout: 30000 });
        await new Promise(r => setTimeout(r, 3000));

        const licensesState = await getVueAppState(page);
        console.log(`  URL: ${licensesState.url}`);
        await captureScreenshot(page, '05_licenses');

        const licensesBodyText = await page.evaluate(() => document.body.innerText);
        const licensesPageContent = await page.content();

        const hasLicenses = licensesPageContent.toLowerCase().includes('license') ||
                            licensesBodyText.includes('软件许可证') ||
                            licensesBodyText.includes('License') ||
                            licensesBodyText.includes('许可证');
        const hasCompliance = licensesBodyText.includes('合规') ||
                             licensesBodyText.includes('Compliance') ||
                             licensesBodyText.includes('即将过期') ||
                             licensesBodyText.includes('Expiring') ||
                             licensesBodyText.includes('总数');

        console.log(`  Has licenses content: ${hasLicenses}`);
        console.log(`  Has compliance info: ${hasCompliance}`);

        results.tests.push({
            name: 'Licenses Management page',
            status: hasLicenses ? 'PASS' : 'FAIL'
        });

        // Test 6: Navigate to Allocations page
        console.log('\n[TEST 6] Navigate to Allocations page');
        console.log('-'.repeat(70));

        await page.goto('http://localhost:5176/software-licenses/allocations', { waitUntil: 'networkidle2', timeout: 30000 });
        await new Promise(r => setTimeout(r, 3000));

        const allocationsState = await getVueAppState(page);
        console.log(`  URL: ${allocationsState.url}`);
        await captureScreenshot(page, '06_allocations');

        const allocationsBodyText = await page.evaluate(() => document.body.innerText);
        const allocationsPageContent = await page.content();

        const hasAllocations = allocationsPageContent.toLowerCase().includes('allocation') ||
                               allocationsBodyText.includes('分配') ||
                               allocationsBodyText.includes('Allocation') ||
                               allocationsBodyText.includes('分配记录');

        console.log(`  Has allocations content: ${hasAllocations}`);

        results.tests.push({
            name: 'Allocations page',
            status: hasAllocations ? 'PASS' : 'FAIL'
        });

        // Test 7: Check API calls
        console.log('\n[TEST 7] API calls summary');
        console.log('-'.repeat(70));

        console.log(`  Total API calls: ${apiCalls.length}`);

        const loginAPI = apiCalls.find(c => c.url.includes('/auth/login/'));
        const usersMeAPI = apiCalls.find(c => c.url.includes('/users/me/'));
        const softwareLicensesAPI = apiCalls.filter(c =>
            c.url.includes('/software-licenses/')
        );

        console.log(`  Login API: ${loginAPI ? `${loginAPI.status}` : 'not called'}`);
        console.log(`  Users/Me API: ${usersMeAPI ? `${usersMeAPI.status}` : 'not called'}`);
        console.log(`  Software Licenses APIs: ${softwareLicensesAPI.length} calls`);

        if (loginAPI && loginAPI.status === 200) {
            results.tests.push({ name: 'Login API call', status: 'PASS' });
        } else {
            results.tests.push({ name: 'Login API call', status: 'FAIL', note: loginAPI ? `Status ${loginAPI.status}` : 'Not called' });
        }

        // Test 8: Check console errors
        console.log('\n[TEST 8] Console errors check');
        console.log('-'.repeat(70));

        const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
        console.log(`  Errors: ${errorMessages.length}`);

        if (errorMessages.length > 0) {
            console.log('  Last errors:');
            errorMessages.slice(-3).forEach(err => {
                console.log(`    - ${err.text.substring(0, 100)}`);
            });
        }

        results.tests.push({
            name: 'Console errors check',
            status: errorMessages.length === 0 ? 'PASS' : 'WARN',
            errors: errorMessages.length
        });

        // Keep browser open for review
        console.log('\n[INFO] Keeping browser open for 5 seconds for review...');
        await new Promise(r => setTimeout(r, 5000));

    } catch (error) {
        console.error(`\n[ERROR] Test failed: ${error.message}`);
        results.errors.push(error.message);
    } finally {
        if (browser) {
            await browser.close();
        }
    }

    // Print summary
    console.log('\n' + '='.repeat(70));
    console.log('TEST SUMMARY');
    console.log('='.repeat(70));

    const passed = results.tests.filter(t => t.status === 'PASS').length;
    const failed = results.tests.filter(t => t.status === 'FAIL').length;
    const warned = results.tests.filter(t => t.status === 'WARN').length;
    const skipped = results.tests.filter(t => t.status === 'SKIP').length;

    console.log(`\nTotal Tests: ${results.tests.length}`);
    console.log(`  PASSED: ${passed}`);
    console.log(`  FAILED: ${failed}`);
    console.log(`  WARNED: ${warned}`);
    console.log(`  SKIPPED: ${skipped}`);

    console.log('\nDetailed Results:');
    results.tests.forEach(test => {
        const icon = test.status === 'PASS' ? '[PASS]' :
                    test.status === 'FAIL' ? '[FAIL]' :
                    test.status === 'WARN' ? '[WARN]' : '[SKIP]';
        console.log(`  ${icon} ${test.name}`);
        if (test.note) {
            console.log(`       Note: ${test.note}`);
        }
    });

    if (results.errors.length > 0) {
        console.log('\nErrors encountered:');
        results.errors.forEach(err => {
            console.log(`  - ${err}`);
        });
    }

    console.log(`\nScreenshots saved to: ${SCREENSHOT_DIR}`);

    return results;
}

// Run the test
testFrontend().catch(console.error);
