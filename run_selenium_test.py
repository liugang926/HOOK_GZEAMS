"""
Frontend Browser Automation Test for Software Licenses Module
Uses Selenium with Chrome WebDriver
"""
import time
import json
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Create screenshots directory
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def capture_screenshot(driver, name):
    """Helper to capture screenshot"""
    path = SCREENSHOT_DIR / f"{name}.png"
    driver.save_screenshot(str(path))
    print(f"  [Screenshot] {path}")
    return path

def safe_find_element(driver, by, value, timeout=5):
    """Safely find element with timeout"""
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None

def safe_find_elements(driver, by, value, timeout=5):
    """Safely find elements with timeout"""
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        return driver.find_elements(by, value)
    except:
        return []

def test_frontend():
    """Main test function"""
    results = {
        "tests": [],
        "errors": [],
        "screenshots": []
    }

    print("\n" + "=" * 70)
    print("BROWSER AUTOMATION TEST: SOFTWARE LICENSES MODULE (Selenium)")
    print("=" * 70)

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--window-size=1280,720')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    # Run in headless mode? Uncomment to hide browser
    # chrome_options.add_argument('--headless')

    # Setup driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Step 1: Navigate to frontend
        print("\n[TEST 1] Navigate to frontend homepage")
        print("-" * 70)
        driver.get('http://localhost:5173')
        time.sleep(3)  # Wait for Vue to render

        capture_screenshot(driver, "01_homepage")

        title = driver.title
        print(f"  Page Title: {title}")
        print(f"  URL: {driver.current_url}")
        results["tests"].append({"name": "Navigate to homepage", "status": "PASS"})

        # Step 2: Check if login is needed
        print("\n[TEST 2] Check for login form")
        print("-" * 70)

        # Get page text
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        page_source = driver.page_source

        need_login = False

        # Check for login indicators
        login_indicators = [
            ('password input', By.TAG_NAME, 'input[type="password"]'),
            ('username input', By.CSS_SELECTOR, 'input[name*="user"], input[placeholder*="用户"]'),
        ]

        for name, by, selector in login_indicators:
            try:
                if by == By.TAG_NAME and '[' in selector:
                    # Handle complex selectors
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = driver.find_elements(by, selector)

                if elements:
                    print(f"  Found: {name}")
                    need_login = True
                    break
            except:
                pass

        # Also check if we're already logged in
        if not need_login:
            if '工作台' in body_text or 'Dashboard' in body_text:
                print("  Already logged in - detected dashboard content")
            elif '退出' in body_text or 'Logout' in body_text:
                print("  Already logged in - detected logout button")

        capture_screenshot(driver, "02_before_login")

        if need_login:
            print("\n[TEST 3] Fill in login credentials")
            print("-" * 70)

            # Try to find username input
            username_input = None
            for selector in [
                'input[name="username"]',
                'input[placeholder*="用户"]',
                'input[placeholder*="账号"]',
                'input[type="text"]',
                '.el-input__inner',
            ]:
                try:
                    username_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if username_input.is_displayed():
                        print(f"  Found username input: {selector}")
                        break
                except:
                    continue

            # Try to find password input
            password_input = None
            for selector in [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="密码"]',
            ]:
                try:
                    password_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input.is_displayed():
                        print(f"  Found password input: {selector}")
                        break
                except:
                    continue

            if username_input:
                username_input.clear()
                username_input.send_keys('admin')
                print("  Entered username: admin")

            if password_input:
                password_input.clear()
                password_input.send_keys('admin123')
                print("  Entered password: ******")

            capture_screenshot(driver, "03_credentials_filled")

            # Find and click login button
            print("\n[TEST 4] Click login button")
            print("-" * 70)

            login_clicked = False
            for selector in [
                'button[type="submit"]',
                'button:contains("登录")',
                '.el-button--primary',
                'button.el-button',
            ]:
                try:
                    if 'contains' in selector:
                        # XPath for contains
                        btn = driver.find_element(By.XPATH, "//button[contains(text(), '登录')]")
                    else:
                        btn = driver.find_element(By.CSS_SELECTOR, selector)

                    if btn.is_displayed():
                        print(f"  Clicking login button: {selector}")
                        btn.click()
                        login_clicked = True
                        break
                except:
                    continue

            if not login_clicked:
                print("  Trying Enter key...")
                from selenium.webdriver.common.keys import Keys
                if password_input:
                    password_input.send_keys(Keys.RETURN)
                elif username_input:
                    username_input.send_keys(Keys.RETURN)

            # Wait for navigation
            time.sleep(5)

        capture_screenshot(driver, "04_after_login")
        print(f"  Current URL: {driver.current_url}")

        # Step 5: Check for software licenses menu
        print("\n[TEST 5] Check for Software Licenses navigation menu")
        print("-" * 70)

        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, 'body').text

        menu_indicators = ['软件许可', '软件目录', '许可证管理', '分配记录']

        found_items = [item for item in menu_indicators if item in body_text]

        print(f"  Menu items found: {found_items}")

        if found_items:
            print("  [PASS] Software licenses menu detected")
            results["tests"].append({"name": "Navigation menu check", "status": "PASS"})
        else:
            print("  [WARN] Software licenses menu not found")
            results["tests"].append({"name": "Navigation menu check", "status": "FAIL"})

        capture_screenshot(driver, "05_menu_check")

        # Step 6: Navigate to software catalog page
        print("\n[TEST 6] Navigate to Software Catalog page")
        print("-" * 70)

        driver.get('http://localhost:5173/software-licenses/software')
        time.sleep(3)

        print(f"  URL: {driver.current_url}")
        capture_screenshot(driver, "06_software_catalog")

        body_text = driver.find_element(By.TAG_NAME, 'body').text
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

        driver.get('http://localhost:5173/software-licenses/licenses')
        time.sleep(3)

        print(f"  URL: {driver.current_url}")
        capture_screenshot(driver, "07_licenses")

        body_text = driver.find_element(By.TAG_NAME, 'body').text
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

        driver.get('http://localhost:5173/software-licenses/allocations')
        time.sleep(3)

        print(f"  URL: {driver.current_url}")
        capture_screenshot(driver, "08_allocations")

        body_text = driver.find_element(By.TAG_NAME, 'body').text
        has_allocations = '分配' in body_text or 'Allocation' in body_text

        print(f"  Has allocations content: {has_allocations}")

        if has_allocations:
            results["tests"].append({"name": "Allocations page", "status": "PASS"})
        else:
            results["tests"].append({"name": "Allocations page", "status": "FAIL"})

        # Step 9: Check for console errors (via browser logs)
        print("\n[TEST 9] Check for browser errors")
        print("-" * 70)

        try:
            logs = driver.get_log('browser')
            error_logs = [log for log in logs if log['level'] == 'SEVERE']
            warning_logs = [log for log in logs if log['level'] == 'WARNING']

            print(f"  Errors: {len(error_logs)}")
            print(f"  Warnings: {len(warning_logs)}")

            if error_logs:
                print("  Error messages:")
                for err in error_logs[-5:]:
                    print(f"    - {err.get('message', err)[:100]}")

            results["tests"].append({
                "name": "Browser errors check",
                "status": "PASS" if len(error_logs) == 0 else "WARN",
                "errors": len(error_logs),
                "warnings": len(warning_logs)
            })
        except Exception as e:
            print(f"  Could not retrieve browser logs: {e}")
            results["tests"].append({"name": "Browser errors check", "status": "SKIP"})

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        results["errors"].append(str(e))
        capture_screenshot(driver, "error_state")

    finally:
        # Keep browser open for review
        print("\n[INFO] Keeping browser open for 5 seconds for review...")
        time.sleep(5)
        driver.quit()

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
        status_icon = "✅" if test["status"] == "PASS" else "❌" if test["status"] == "FAIL" else "⚠️" if test["status"] == "WARN" else "⏭️"
        print(f"  {status_icon} {test['name']}: {test['status']}")

    if results["errors"]:
        print("\nErrors encountered:")
        for err in results["errors"]:
            print(f"  - {err}")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR.absolute()}")

    return results

if __name__ == '__main__':
    test_frontend()
