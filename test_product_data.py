from playwright.sync_api import sync_playwright
import csv
import os
import logging
from datetime import datetime

def capture_failure_screenshot(page, test_name):
    """Capture screenshot on test failure"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_path = f'screenshots/failure_{test_name}_{timestamp}.png'
    page.screenshot(path=screenshot_path)
    logging.info(f"Screenshot captured: {screenshot_path}")

def scrape_product_data():
    """Scrape product data from the website"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Login first
            logging.info("Navigating to website")
            page.goto('https://www.saucedemo.com')
            
            logging.info("Logging in")
            page.fill('#user-name', 'standard_user')
            page.fill('#password', 'secret_sauce')
            page.click('#login-button')
            
            # Wait for the inventory page to load
            logging.info("Waiting for inventory page to load")
            page.wait_for_load_state('networkidle')
            
            # Verify we're on the inventory page
            assert '/inventory.html' in page.url, "Failed to reach inventory page"
            
            # Get all product elements
            logging.info("Collecting product data")
            products = page.locator('.inventory_item').all()
            
            # Prepare data for CSV
            product_data = []
            for product in products:
                data = {
                    'name': product.locator('.inventory_item_name').text_content(),
                    'description': product.locator('.inventory_item_desc').text_content(),
                    'price': product.locator('.inventory_item_price').text_content(),
                    'image_url': product.locator('img.inventory_item_img').get_attribute('src')
                }
                product_data.append(data)
            
            # Save to CSV
            csv_file = 'products.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['name', 'description', 'price', 'image_url'])
                writer.writeheader()
                writer.writerows(product_data)
            
            logging.info(f"Successfully saved {len(product_data)} products to {csv_file}")
            return True
            
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            capture_failure_screenshot(page, "product_data")
            raise
            
        finally:
            browser.close()

def run_all_tests():
    """Run all product data tests"""
    logging.info("Starting product data tests")
    
    try:
        success = scrape_product_data()
        if success:
            logging.info("All product data tests completed successfully")
            return True
        else:
            logging.error("Product data tests failed")
            return False
    except Exception as e:
        logging.error(f"Product data tests failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_all_tests() 