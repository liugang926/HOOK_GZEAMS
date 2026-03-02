"""
Frontend Browser Automation Test using Microsoft Edge WebDriver
Edge is pre-installed on Windows and more reliable
"""
import time
import json
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Create screenshots directory
SCREENSHOT_DIR = Path("test_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def capture_screenshot(driver, name):
    """Helper to capture screenshot"""
    path = SCREENSHOT_DIR / f"{name}.png"
    driver.save_screenshot(str(path))
    print(f"  [Screenshot] {path}")
    return path

def test_frontend():
    """Main test function"""
    results = {
        "tests": [],
        "errors": [],
        "screenshots": []
    }

    print("\n" + "=" * 70)
    print("BROWSER AUTOMATION TEST: SOFTWARE LICENSES MODULE (Edge WebDriver)")
    print("=" * 70)

    # Setup Edge options
    edge_options = Options()
    edge_options.add_argument('--window-size=1280,720')
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    # edge_options.add_argument('--headless')  # Uncomment for headless mode

    # Setup driver
    try:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"  [ERROR] Could not initialize Edge driver: {e}")
        print("  Trying default system Edge...")
        driver = webdriver.Edge(options=edge_options)

    try:
        # Step 1: Navigate to frontend
        print("\n[TEST 1] Navigate to frontend homepage")
        print("-" * 70)
        driver.get('http://localhost:5173')
        time.sleep(4)  # Wait for Vue to render

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

        print(f"  Page text length: {len(body_text)} chars")
        print(f"  Page contains 'GZEAMS': {'GZEAMS' in page_source}")
        print(f"  Page contains '工作台': {'工作台' in body_text}")
        print(f"  Page contains '软件': {'软件' in body_text}")

        # Check for password input to determine if login is needed
        password_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
        need_login = len(password_inputs) > 0

        if need_login:
            print("  Password input found - login required")
        else:
            print("  No password input - may already be logged in")

            # Check if we're already logged in
            if '工作台' in body_text or 'Dashboard' in body_text:
                print("  Already logged in - detected dashboard content")

        capture_screenshot(driver, "02_before_login")

        if need_login:
            print("\n[TEST 3] Fill in login credentials")
            print("-" * 70)

            # Find username input
            username_input = None
            for selector in [
                'input[name="username"]',
                'input[placeholder*="用户"]',
                'input[placeholder*="账号"]',
            ]:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        username_input = elements[0]
                        print(f"  Found username input: {selector}")
                        break
                except:
                    continue

            # If not found, try first visible text input
            if not username_input:
                text_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
                for inp in text_inputs:
                    try:
                        if inp.is_displayed():
                            username_input = inp
                            print("  Using first visible text input")
                            break
                    except:
                        pass

            # Find password input
            password_input = None
            password_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
            for inp in password_inputs:
                try:
                    if inp.is_displayed():
                        password_input = inp
                        print("  Found visible password input")
                        break
                except:
                    pass

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
            for xpath_selector in [
                "//button[contains(text(), '登录')]",
                "//button[@type='submit']",
                "//button[contains(@class, 'el-button--primary')]",
            ]:
                try:
                    btn = driver.find_element(By.XPATH, xpath_selector)
                    if btn.is_displayed():
                        print(f"  Clicking login button: {xpath_selector}")
                        btn.click()
                        login_clicked = True
                        time.sleep(1)
                        break
                except:
                    continue

            if not login_clicked:
                print("  Trying Enter key on password field...")
                from selenium.webdriver.common.keys import Keys
                if password_input:
                    password_input.send_keys(Keys.RETURN)
                elif username_input:
                    username_input.send_keys(Keys.RETURN)

            # Wait for navigation
            print("  Waiting for page load...")
            time.sleep(6)

        capture_screenshot(driver, "04_after_login")
        print(f"  Current URL: {driver.current_url}")

        # Get updated body text
        body_text = driver.find_element(By.TAG_NAME, 'body').text

        # Step 5: Check for software licenses menu
        print("\n[TEST 5] Check for Software Licenses navigation menu")
        print("-" * 70)

        menu_indicators = ['软件许可', '软件目录', '许可证管理', '分配记录']

        found_items = [item for item in menu_indicators if item in body_text]

        print(f"  Menu items found: {found_items}")

        if found_items:
            print("  [PASS] Software licenses menu detected")
            results["tests"].append({"name": "Navigation menu check", "status": "PASS"})
        else:
            print("  [WARN] Software licenses menu not found in body text")
            # Check page source as well
            page_source = driver.page_source
            for item in menu_indicators:
                if item in page_source:
                    print(f"  But found '{item}' in page source")
            results["tests"].append({"name": "Navigation menu check", "status": "PARTIAL"})

        capture_screenshot(driver, "05_menu_check")

        # Step 6: Navigate to software catalog page
        print("\n[TEST 6] Navigate to Software Catalog page")
        print("-" * 70)

        driver.get('http://localhost:5173/software-licenses/software')
        time.sleep(4)

        print(f"  URL: {driver.current_url}")
        capture_screenshot(driver, "06_software_catalog")

        body_text = driver.find_element(By.TAG_NAME, 'body').text
        has_software_catalog = '软件目录' in body_text or 'Software Catalog' in body_text or 'software' in driver.page_source.lower()
        has_create_button = '新建软件' in body_text or 'Create' in body_text or '新建' in body_text

        print(f"  Has '软件目录': {has_software_catalog}")
        print(f"  Has '新建' button: {has_create_button}")

        if has_software_catalog:
            results["tests"].append({"name": "Software Catalog page", "status": "PASS"})
        else:
            results["tests"].append({"name": "Software Catalog page", "status": "FAIL"})

        # Step 7: Navigate to licenses page
        print("\n[TEST 7] Navigate to Licenses Management page")
        print("-" * 70)

        driver.get('http://localhost:5173/software-licenses/licenses')
        time.sleep(4)

        print(f"  URL: {driver.current_url}")
        capture_screenshot(driver, "07_licenses")

        body_text = driver.find_element(By.TAG_NAME, 'body').text
        has_licenses = '软件许可证' in body_text or 'License' in body_text
        has_compliance = any(x in body_text for x in ['合规', 'Compliance', '即将过期', 'Expiring', '总数'])

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
        time.sleep(4)

        print(f"  URL: {driver.current_url}")
        capture_screenshot(driver, "08_allocations")

        body_text = driver.find_element(By.TAG_NAME, 'body').text
        has_allocations = '分配' in body_text or 'Allocation' in body_text

        print(f"  Has allocations content: {has_allocations}")

        if has_allocations:
            results["tests"].append({"name": "Allocations page", "status": "PASS"})
        else:
            results["tests"].append({"name": "Allocations page", "status": "FAIL"})

        # Step 9: Check page title consistency
        print("\n[TEST 9] Check page titles")
        print("-" * 70)

        titles_good = 'GZEAMS' in driver.title
        print(f"  Page title contains GZEAMS: {titles_good}")

        results["tests"].append({
            "name": "Page title check",
            "status": "PASS" if titles_good else "FAIL"
        })

    except Exception as e:
        import traceback
        print(f"\n[ERROR] Test failed: {e}")
        print(traceback.format_exc())
        results["errors"].append(str(e))
        try:
            capture_screenshot(driver, "error_state")
        except:
            pass

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
    partial = sum(1 for t in results["tests"] if t["status"] == "PARTIAL")

    print(f"\nTotal Tests: {len(results['tests'])}")
    print(f"  PASSED: {passed}")
    print(f"  FAILED: {failed}")
    print(f"  PARTIAL: {partial}")

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
    test_frontend()
