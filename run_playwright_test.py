"""
Frontend Browser Automation Test using Playwright (async)
"""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Create screenshots directory
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

async def capture_screenshot(page, name):
    """Helper to capture screenshot"""
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path), full_page=True)
    print(f"  [Screenshot] {path}")
    return path

async def test_frontend():
    """Main test function"""
    results = {
        "tests": [],
        "errors": [],
        "screenshots": []
    }

    print("\n" + "=" * 70)
    print("BROWSER AUTOMATION TEST: SOFTWARE LICENSES MODULE (Playwright Async)")
    print("=" * 70)

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )

        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='zh-CN'
        )

        page = await context.new_page()

        # Enable console log capture
        console_messages = []
        def on_console(msg):
            console_messages.append({'type': msg.type, 'text': msg.text})

        page.on('console', on_console)

        try:
            # Step 1: Navigate to frontend
            print("\n[TEST 1] Navigate to frontend homepage")
            print("-" * 70)
            await page.goto('http://localhost:5173', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            await capture_screenshot(page, "01_homepage")

            title = await page.title()
            url = page.url
            print(f"  Page Title: {title}")
            print(f"  URL: {url}")
            results["tests"].append({"name": "Navigate to homepage", "status": "PASS"})

            # Step 2: Check page content
            print("\n[TEST 2] Check page content")
            print("-" * 70)

            body_text = await page.inner_text('body')
            page_content = await page.content()

            print(f"  Page text length: {len(body_text)} chars")
            print(f"  Contains 'GZEAMS': {'GZEAMS' in page_content}")
            print(f"  Contains '工作台': {'工作台' in body_text}")
            print(f"  Contains '软件': {'软件' in body_text}")

            await capture_screenshot(page, "02_page_content")

            # Check if login is needed
            password_inputs = await page.query_selector_all('input[type="password"]')
            need_login = len(password_inputs) > 0

            if need_login:
                print("  Password input found - login may be required")
            else:
                print("  No password input - checking if already logged in...")
                if '工作台' in body_text or 'Dashboard' in body_text:
                    print("  Already logged in - detected dashboard content")

            # Step 3: Navigate to software catalog directly
            print("\n[TEST 3] Navigate to Software Catalog page")
            print("-" * 70)

            await page.goto('http://localhost:5173/software-licenses/software', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            print(f"  URL: {page.url}")
            await capture_screenshot(page, "03_software_catalog")

            body_text = await page.inner_text('body')
            page_content = await page.content()

            has_software = any(x in body_text or x in page_content for x in ['软件目录', 'Software Catalog', 'software'])
            has_create = '新建' in body_text or 'Create' in body_text

            print(f"  Has software content: {has_software}")
            print(f"  Has create button: {has_create}")

            if has_software:
                results["tests"].append({"name": "Software Catalog page", "status": "PASS"})
            else:
                results["tests"].append({"name": "Software Catalog page", "status": "FAIL"})

            # Step 4: Navigate to licenses page
            print("\n[TEST 4] Navigate to Licenses Management page")
            print("-" * 70)

            await page.goto('http://localhost:5173/software-licenses/licenses', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            print(f"  URL: {page.url}")
            await capture_screenshot(page, "04_licenses")

            body_text = await page.inner_text('body')
            page_content = await page.content()

            has_licenses = any(x in body_text or x in page_content for x in ['软件许可证', 'License', 'license'])
            has_compliance = any(x in body_text for x in ['合规', 'Compliance', '即将过期', 'Expiring', '总数'])

            print(f"  Has licenses content: {has_licenses}")
            print(f"  Has compliance info: {has_compliance}")

            if has_licenses:
                results["tests"].append({"name": "Licenses Management page", "status": "PASS"})
            else:
                results["tests"].append({"name": "Licenses Management page", "status": "FAIL"})

            # Step 5: Navigate to allocations page
            print("\n[TEST 5] Navigate to Allocations page")
            print("-" * 70)

            await page.goto('http://localhost:5173/software-licenses/allocations', wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            print(f"  URL: {page.url}")
            await capture_screenshot(page, "05_allocations")

            body_text = await page.inner_text('body')
            page_content = await page.content()

            has_allocations = any(x in body_text or x in page_content for x in ['分配', 'Allocation', 'allocation'])

            print(f"  Has allocations content: {has_allocations}")

            if has_allocations:
                results["tests"].append({"name": "Allocations page", "status": "PASS"})
            else:
                results["tests"].append({"name": "Allocations page", "status": "FAIL"})

            # Step 6: Check for console errors
            print("\n[TEST 6] Check for console errors")
            print("-" * 70)

            error_messages = [msg for msg in console_messages if msg['type'] == 'error']
            warning_messages = [msg for msg in console_messages if msg['type'] == 'warning']

            print(f"  Errors: {len(error_messages)}")
            print(f"  Warnings: {len(warning_messages)}")

            if error_messages:
                print("  Error messages:")
                for err in error_messages[-5:]:
                    print(f"    - {err['text'][:100]}")

            results["tests"].append({
                "name": "Console errors check",
                "status": "PASS" if len(error_messages) == 0 else "WARN",
                "errors": len(error_messages),
                "warnings": len(warning_messages)
            })

        except Exception as e:
            import traceback
            print(f"\n[ERROR] Test failed: {e}")
            print(traceback.format_exc())
            results["errors"].append(str(e))
            try:
                await capture_screenshot(page, "error_state")
            except:
                pass

        finally:
            # Keep browser open for review
            print("\n[INFO] Keeping browser open for 5 seconds for review...")
            await asyncio.sleep(5)
            await browser.close()

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    failed = sum(1 for t in results["tests"] if t["status"] == "FAIL")
    warned = sum(1 for t in results["tests"] if t["status"] == "WARN")

    print(f"\nTotal Tests: {len(results['tests'])}")
    print(f"  PASSED: {passed}")
    print(f"  FAILED: {failed}")
    print(f"  WARNED: {warned}")

    print("\nDetailed Results:")
    for test in results["tests"]:
        status_icon = "✅" if test["status"] == "PASS" else "❌" if test["status"] == "FAIL" else "⚠️"
        print(f"  {status_icon} {test['name']}: {test['status']}")

    if results["errors"]:
        print("\nErrors encountered:")
        for err in results["errors"]:
            print(f"  - {err}")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR.absolute()}")

    return results

if __name__ == '__main__':
    # Set event loop policy for Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(test_frontend())
