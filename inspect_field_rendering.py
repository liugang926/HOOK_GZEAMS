"""
Script to inspect actual field rendering in the Asset form page.
Uses Playwright to navigate to the page and inspect the DOM.
"""
from playwright.sync_api import sync_playwright
import json
import time

AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcwMTkxNjQ2LCJpYXQiOjE3NzAxODQ0NDYsImp0aSI6ImE2MWIxNDYyYzFiNjRlMTdiMjFlYjhlMWY2YjVlNWNjIiwidXNlcl9pZCI6ImUwYzlkYWRhLTg5YTYtNDQ1Zi1iNTU1LTI5OGZlZGU2Y2RhMyJ9.lF_gl9hCYktOYyEamRWeNMfJPkfFc17zl8qAoUxFrHg"

def inspect_asset_fields():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Set auth token in localStorage before navigating
        page.goto("http://localhost:5173")
        page.evaluate(f"""() => {{
            localStorage.setItem('gzeams_access_token', '{AUTH_TOKEN}');
            localStorage.setItem('gzeams_user_info', JSON.stringify({{
                id: 'e0c9dada-89a6-445f-b555-298fede6cda3',
                username: 'admin',
                organization: 'default-org'
            }}));
        }}""")

        # Navigate to Asset list
        print("Navigating to Asset list...")
        page.goto("http://localhost:5173/assets")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Try to click on first asset row
        try:
            first_row = page.locator('.el-table__row').first
            if first_row.count() > 0:
                print("Clicking on first asset...")
                first_row.click()
                page.wait_for_timeout(2000)

                # Now inspect the detail page
                print("\n=== INSPECTING DETAIL PAGE ===")
                detail_content = page.content()

                # Look for QR code field
                qr_code_elements = page.locator('[class*="qr-code"]').all()
                print(f"QR code elements found: {len(qr_code_elements)}")

                # Look for images field
                image_elements = page.locator('[class*="image"]').all()
                print(f"Image elements found: {len(image_elements)}")

                # Look for attachment/file upload elements
                file_elements = page.locator('[class*="upload"], [class*="attachment"]').all()
                print(f"File upload elements found: {len(file_elements)}")

                # Look for input elements (check if fields are rendering as text inputs)
                input_elements = page.locator('input[type="text"]').all()
                print(f"Text input elements found: {len(input_elements)}")

                # Take screenshot
                page.screenshot(path='screenshots/asset_detail_inspection.png', full_page=True)
                print("Screenshot saved to screenshots/asset_detail_inspection.png")

                # Get all field labels
                print("\n=== FIELD LABELS FOUND ===")
                labels = page.locator('.field-label, .el-form-item__label').all()
                for label in labels[:20]:  # First 20 labels
                    print(f"  - {label.text_value()}")

        except Exception as e:
            print(f"Error clicking asset: {e}")

        # Now try to navigate to edit page
        try:
            print("\n=== NAVIGATING TO EDIT PAGE ===")
            page.goto("http://localhost:5173/assets")
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            first_row = page.locator('.el-table__row').first
            if first_row.count() > 0:
                # Try to find and click edit button
                edit_buttons = page.locator('button:has-text("编辑"), button:has-text("Edit")').all()
                if edit_buttons:
                    edit_buttons[0].click()
                    page.wait_for_timeout(2000)

                    # Inspect edit page
                    print("\n=== INSPECTING EDIT PAGE ===")

                    # Check for field types
                    input_elements = page.locator('input[type="text"]').all()
                    print(f"Text input elements on edit page: {len(input_elements)}")

                    # Get field labels and their following elements
                    print("\n=== FIELDS ON EDIT PAGE ===")
                    form_items = page.locator('.el-form-item').all()
                    for i, item in enumerate(form_items[:15]):
                        label = item.locator('.el-form-item__label').text_value()
                        # Check what type of input follows
                        input_type = item.locator('input').get_attribute('type') or "unknown"
                        has_select = item.locator('el-select').count() > 0
                        has_textarea = item.locator('textarea').count() > 0
                        has_upload = item.locator('[class*="upload"]').count() > 0

                        print(f"  {i+1}. {label}: input_type={input_type}, select={has_select}, textarea={has_textarea}, upload={has_upload}")

                    page.screenshot(path='screenshots/asset_edit_inspection.png', full_page=True)
                    print("Screenshot saved to screenshots/asset_edit_inspection.png")

        except Exception as e:
            print(f"Error on edit page: {e}")

        print("\nPress Enter to close browser...")
        input()
        browser.close()

if __name__ == "__main__":
    import os
    os.makedirs('screenshots', exist_ok=True)
    inspect_asset_fields()
