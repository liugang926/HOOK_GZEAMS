"""
Frontend Browser Automation Test for Software Licenses Module
Tests the NEWSEAMS frontend with admin credentials using Playwright
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import json
import time
import os
from pathlib import Path

# Create screenshots directory
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def capture_screenshot(page, name, full_page=False):
    """Helper to capture screenshot"""
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    print(f"  [Screenshot] {path}")
    return path

def test_frontend():
    """Main test function"""
    results = {
        "tests": [],
        "errors": [],
        "screenshots": []
    }

    with sync_playwright() as p:
        print("\n" + "=" * 70)
        print("BROWSER AUTOMATION TEST: SOFTWARE LICENSES MODULE")
        print("=" * 70)

        # Launch browser (headless=False to see what's happening)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='zh-CN'
        )

        # Enable console log capture
        console_messages = []
        def on_console(msg):
            console_messages.append({'type': msg.type, 'text': msg.text})
        page = context.new_page()
        page.on('console', on_console)

        try:
            # Step 1: Navigate to frontend
            print("\n[TEST 1] Navigate to frontend homepage")
            print("-" * 70)
            page.goto('http://localhost:5173', wait_until='networkidle', timeout=30000)
            capture_screenshot(page, "01_homepage")

            title = page.title()
            print(f"  Page Title: {title}")
            print(f"  URL: {page.url}")
            results["tests"].append({"name": "Navigate to homepage", "status": "PASS"})

            # Step 2: Check if login is needed
            print("\n[TEST 2] Check for login form")
            print("-" * 70)

            # Wait a bit for Vue to render
            page.wait_for_timeout(2000)

            # Check if we need to login
            need_login = False
            try:
                # Look for login elements - checking multiple possible selectors
                login_indicators = [
                    'input[type="password"]',
                    'input[placeholder*="密码"]',
                    'input[placeholder*="password"]',
                    'el-input[type="password"]',
                    '.login-form',
                    '#login'
                ]

                for selector in login_indicators:
                    try:
                        if page.locator(selector).count() > 0:
                            print(f"  Found login indicator: {selector}")
                            need_login = True
                            break
                    except:
                        continue

                if not need_login:
                    # Check if we're already on dashboard
                    body_text = page.locator('body').inner_text()
                    if '工作台' in body_text or 'Dashboard' in body_text:
                        print("  Already logged in - detected dashboard content")
                    elif page.url != 'http://localhost:5173/':
                        print(f"  Already logged in - redirected to {page.url}")
                    else:
                        # Check if app div has content
                        app_content = page.locator('#app').inner_text()
                        if len(app_content) > 100:
                            print("  App has content, may be logged in")
                        else:
                            print("  Checking for login button...")
                            # Check for login button
                            login_btn = page.locator('button:has-text("登录"), button:has-text("Login"), .login-btn')
                            if login_btn.count() > 0:
                                need_login = True
                                print("  Found login button")
            except Exception as e:
                print(f"  Error checking login: {e}")
                need_login = True

            capture_screenshot(page, "02_before_login", full_page=True)

            if need_login:
                print("\n[TEST 3] Fill in login credentials")
                print("-" * 70)

                # Try multiple selector strategies
                username_filled = False
                password_filled = False

                # Strategy 1: By placeholder
                username_selectors = [
                    'input[placeholder*="用户"]',
                    'input[placeholder*="账号"]',
                    'input[placeholder*="username"]',
                    'input[name="username"]',
                    'input[type="text"]',
                    '.el-input__inner'
                ]

                for selector in username_selectors:
                    try:
                        input = page.locator(selector).first
                        if input.is_visible(timeout=1000):
                            print(f"  Filling username with selector: {selector}")
                            input.fill('admin')
                            username_filled = True
                            break
                    except:
                        continue

                if not username_filled:
                    print("  Could not find username input, trying click-and-fill...")
                    # Try to find by text label
                    all_inputs = page.locator('input[type="text"]').all()
                    for inp in all_inputs:
                        try:
                            if inp.is_visible():
                                inp.click()
                                inp.fill('admin')
                                username_filled = True
                                print("  Filled first visible text input")
                                break
                        except:
                            pass

                # Password
                password_selectors = [
                    'input[placeholder*="密码"]',
                    'input[placeholder*="password"]',
                    'input[name="password"]',
                    'input[type="password"]'
                ]

                for selector in password_selectors:
                    try:
                        input = page.locator(selector).first
                        if input.is_visible(timeout=1000):
                            print(f"  Filling password with selector: {selector}")
                            input.fill('admin123')
                            password_filled = True
                            break
                    except:
                        continue

                capture_screenshot(page, "03_credentials_filled")

                if username_filled and password_filled:
                    print("\n[TEST 4] Click login button")
                    print("-" * 70)

                    login_btn_selectors = [
                        'button[type="submit"]',
                        'button:has-text("登录")',
                        'button:has-text("Login")',
                        '.el-button--primary',
                        '.login-btn'
                    ]

                    clicked = False
                    for selector in login_btn_selectors:
                        try:
                            btn = page.locator(selector).first
                            if btn.is_visible(timeout=1000):
                                print(f"  Clicking button: {selector}")
                                btn.click()
                                clicked = True
                                break
                        except:
                            continue

                    if not clicked:
                        print("  Could not find login button, trying Enter key...")
                        page.keyboard.press('Enter')

                    # Wait for navigation
                    page.wait_for_timeout(3000)
                else:
                    print("  WARNING: Could not fill login form")
                    results["errors"].append("Could not fill login form")

            capture_screenshot(page, "04_after_login", full_page=True)
            print(f"  Current URL: {page.url}")

            # Step 5: Check for software licenses menu
            print("\n[TEST 5] Check for Software Licenses navigation menu")
            print("-" * 70)

            page.wait_for_timeout(2000)
            body_text = page.locator('body').inner_text()

            menu_found = False
            menu_indicators = ['软件许可', '软件目录', '许可证管理', '分配记录']

            found_items = []
            for item in menu_indicators:
                if item in body_text:
                    found_items.append(item)

            print(f"  Menu items found: {found_items}")

            if found_items:
                print("  [PASS] Software licenses menu detected")
                results["tests"].append({"name": "Navigation menu check", "status": "PASS"})
                menu_found = True
            else:
                print("  [WARN] Software licenses menu not found in page text")
                results["tests"].append({"name": "Navigation menu check", "status": "FAIL", "note": "Menu not found"})

            capture_screenshot(page, "05_menu_check", full_page=True)

            # Step 6: Navigate to software catalog page
            print("\n[TEST 6] Navigate to Software Catalog page")
            print("-" * 70)

            page.goto('http://localhost:5173/software-licenses/software', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)

            print(f"  URL: {page.url}")
            capture_screenshot(page, "06_software_catalog", full_page=True)

            body_text = page.locator('body').inner_text()
            has_software_catalog = '软件目录' in body_text or 'Software Catalog' in body_text
            has_create_button = '新建软件' in body_text or 'Create' in body_text

            print(f"  Has '软件目录': {has_software_catalog}")
            print(f"  Has '新建软件' button: {has_create_button}")

            if has_software_catalog:
                results["tests"].append({"name": "Software Catalog page", "status": "PASS"})
            else:
                results["tests"].append({"name": "Software Catalog page", "status": "FAIL"})

            # Step 7: Navigate to licenses page
            print("\n[TEST 7] Navigate to Licenses Management page")
            print("-" * 70)

            page.goto('http://localhost:5173/software-licenses/licenses', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)

            print(f"  URL: {page.url}")
            capture_screenshot(page, "07_licenses", full_page=True)

            body_text = page.locator('body').inner_text()
            has_licenses = '软件许可证' in body_text or 'License' in body_text
            has_compliance = any(x in body_text for x in ['合规', 'Compliance', '即将过期', 'Expiring'])

            print(f"  Has licenses content: {has_licenses}")
            print(f"  Has compliance info: {has_compliance}")

            if has_licenses:
                results["tests"].append({"name": "Licenses Management page", "status": "PASS"})
            else:
                results["tests"].append({"name": "Licenses Management page", "status": "FAIL"})

            # Step 8: Navigate to allocations page
            print("\n[TEST 8] Navigate to Allocations page")
            print("-" * 70)

            page.goto('http://localhost:5173/software-licenses/allocations', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)

            print(f"  URL: {page.url}")
            capture_screenshot(page, "08_allocations", full_page=True)

            body_text = page.locator('body').inner_text()
            has_allocations = '分配' in body_text or 'Allocation' in body_text

            print(f"  Has allocations content: {has_allocations}")

            if has_allocations:
                results["tests"].append({"name": "Allocations page", "status": "PASS"})
            else:
                results["tests"].append({"name": "Allocations page", "status": "FAIL"})

            # Step 9: Check for JavaScript errors
            print("\n[TEST 9] Check for JavaScript errors")
            print("-" * 70)

            error_messages = [msg for msg in console_messages if msg['type'] == 'error']
            warning_messages = [msg for msg in console_messages if msg['type'] == 'warning']

            print(f"  Errors: {len(error_messages)}")
            print(f"  Warnings: {len(warning_messages)}")

            if error_messages:
                print("  Error messages:")
                for err in error_messages[-5:]:  # Last 5 errors
                    print(f"    - {err['text'][:100]}")

            results["tests"].append({
                "name": "JavaScript errors check",
                "status": "PASS" if len(error_messages) == 0 else "WARN",
                "errors": len(error_messages),
                "warnings": len(warning_messages)
            })

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            results["errors"].append(str(e))
            capture_screenshot(page, "error_state", full_page=True)

        finally:
            # Keep browser open for a moment to see final state
            print("\n[INFO] Keeping browser open for 3 seconds for review...")
            page.wait_for_timeout(3000)
            browser.close()

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
        if "note" in test:
            print(f"     Note: {test['note']}")

    if results["errors"]:
        print("\nErrors encountered:")
        for err in results["errors"]:
            print(f"  - {err}")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR.absolute()}")

    return results

if __name__ == '__main__':
    test_frontend()
