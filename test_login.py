from playwright.sync_api import sync_playwright, expect
import json
import time
import os
from datetime import datetime
import logging

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/test_run_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # This will also print to console
        ]
    )
    return log_file

def load_test_cases():
    """Load test cases from JSON file"""
    with open('test_data/login_test_cases.json', 'r') as f:
        data = json.load(f)
    return data['test_cases']

def log_form_validation_error(test_case_name, error_message):
    """Log form validation errors to a separate file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Test Case: {test_case_name} - Error: {error_message}\n"
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Append to validation errors log
    with open('logs/validation_errors.log', 'a') as f:
        f.write(log_entry)

def capture_failure_screenshot(page, test_case_name):
    logging.info(f"Capturing failure screenshot for test case: {test_case_name}")
    # Create screenshots directory if it doesn't exist
    os.makedirs('screenshots', exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    screenshot_path = f'screenshots/failure_{test_case_name}_{timestamp}.png'
    
    # Take screenshot
    page.screenshot(path=screenshot_path)
    logging.info(f"Screenshot captured: {screenshot_path}")

def perform_additional_validations(page, test_case):
    if 'additional_validations' not in test_case:
        return

    validations = test_case['additional_validations']
    logging.info(f"Performing additional validations for test case: {test_case['name']}")
    
    if validations.get('check_inventory_count'):
        logging.info("Checking inventory count")
        inventory_items = page.locator('.inventory_item').all()
        assert len(inventory_items) > 0, "Inventory should contain items"
        logging.info(f"Verified inventory contains {len(inventory_items)} items")
    
    if validations.get('check_cart_empty'):
        logging.info("Checking if cart is empty")
        cart_badge = page.locator('.shopping_cart_badge')
        assert not cart_badge.is_visible(), "Cart should be empty initially"
        logging.info("Verified cart is empty")
    
    if validations.get('check_menu_visible'):
        logging.info("Checking if menu button is visible")
        menu_button = page.locator('#react-burger-menu-btn')
        assert menu_button.is_visible(), "Menu button should be visible"
        logging.info("Verified menu button is visible")
        
    if validations.get('check_nonexistent_element'):
        logging.info("Checking for nonexistent element (expected to fail)")
        nonexistent_element = page.locator('#this-element-does-not-exist')
        assert not nonexistent_element.is_visible(), "This element should not be visible as it doesn't exist"
        logging.info("Verified nonexistent element is not visible")

def run_login_test(page, test_case):
    """Run a single login test case"""
    test_case_name = test_case['name']
    username = test_case['username']
    password = test_case['password']
    expected_result = test_case['expected_result']
    expected_error_message = test_case.get('expected_error_message', None)
    
    logging.info(f"Starting test case: {test_case_name}")
    logging.info(f"Username: {username}")
    
    try:
        # Navigate to website
        logging.info("Navigating to website")
        page.goto('https://www.saucedemo.com/')
        
        # Fill login form
        logging.info("Filling login form")
        page.fill('#user-name', username)
        page.fill('#password', password)
        
        # Click login button
        logging.info("Clicking login button")
        page.click('#login-button')
        
        # Wait for page load
        logging.info("Waiting for page load")
        start_time = time.time()
        page.wait_for_load_state('networkidle')
        end_time = time.time()
        
        # Calculate response time
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        logging.info(f"Response time: {response_time:.2f}ms")
        
        # Check response time against threshold
        threshold = 6000 if username == 'performance_glitch_user' else 4000
        logging.info(f"Checking response time against threshold: {threshold}ms")
        assert response_time <= threshold, f"Response time {response_time:.2f}ms exceeded threshold of {threshold}ms"
        logging.info("Response time check passed")
        
        # Verify URL contains expected path
        logging.info("Verifying URL contains expected path")
        if expected_result == 'success':
            assert '/inventory.html' in page.url, "Failed to reach inventory page"
            logging.info(f"Successfully logged in as {username}")
            
            # Perform additional validations for successful login
            logging.info(f"Performing additional validations for test case: {test_case_name}")
            
            # Check inventory count
            logging.info("Checking inventory count")
            inventory_items = page.locator('.inventory_item').all()
            assert len(inventory_items) == 6, "Inventory should contain 6 items"
            logging.info(f"Verified inventory contains {len(inventory_items)} items")
            
            # Check if cart is empty
            logging.info("Checking if cart is empty")
            cart_badge = page.locator('.shopping_cart_badge')
            assert not cart_badge.is_visible(), "Cart should be empty"
            logging.info("Verified cart is empty")
            
            # Check if menu button is visible
            logging.info("Checking if menu button is visible")
            menu_button = page.locator('#react-burger-menu-btn')
            assert menu_button.is_visible(), "Menu button should be visible"
            logging.info("Verified menu button is visible")
            
        else:
            # Check for error message
            error_element = page.locator('[data-test="error"]')
            assert error_element.is_visible(), "Error message should be visible"
            error_message = error_element.text_content()
            logging.info(f"Received error message: {error_message}")
            
            if expected_error_message:
                assert expected_error_message in error_message, \
                    f"Expected error message '{expected_error_message}' not found in '{error_message}'"
        
        logging.info(f"Test case completed: {test_case_name}")
        
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        capture_failure_screenshot(page, test_case_name)
        log_form_validation_error(test_case_name, str(e))
        raise

def run_all_tests():
    """Run all test cases"""
    logging.info("Starting test suite")
    
    try:
        test_cases = load_test_cases()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            for test_case in test_cases:
                run_login_test(page, test_case)
            
            browser.close()
            
        logging.info("Test suite completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"Test suite failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Ensure test_data directory exists
    os.makedirs('test_data', exist_ok=True)
    run_all_tests() 