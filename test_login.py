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
    logging.info("Loading test cases from JSON file")
    with open('test_data/login_test_cases.json', 'r') as file:
        test_cases = json.load(file)['test_cases']
        logging.info(f"Loaded {len(test_cases)} test cases")
        return test_cases

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
    max_response_time = test_case.get('max_response_time_ms', 4000)  # Default to 2000ms if not specified
    
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
        
        # Click login button and measure response time
        logging.info("Clicking login button")
        start_time = time.time()
        page.click('#login-button')
        
        # Wait for navigation
        logging.info("Waiting for page load")
        page.wait_for_load_state('networkidle')
        end_time = time.time()
        
        # Check for form validation error message in the UI
        error_element = page.locator('[data-test="error"]')
        if error_element.is_visible():
            error_message = error_element.text_content()
            logging.warning(f"Form validation error detected: {error_message}")
            log_form_validation_error(test_case_name, error_message)
        
        # Calculate and log response time
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        logging.info(f"Response time: {response_time:.2f}ms")
        
        # Check response time
        logging.info(f"Checking response time against threshold: {max_response_time}ms")
        if response_time > max_response_time:
            error_msg = f"[{test_case_name}] Response time {response_time:.2f}ms exceeded maximum threshold of {max_response_time}ms"
            logging.error(error_msg)
            log_form_validation_error(test_case_name, error_msg)
            raise AssertionError(error_msg)
        logging.info("Response time check passed")
        
        # Verify URL for success cases
        if expected_result == "success":
            expected_url = test_case.get('expected_url_contains', '/inventory.html')  # Default to inventory page
            logging.info("Verifying URL contains expected path")
            current_url = page.url
            if expected_url not in current_url:
                error_msg = f"[{test_case_name}] Expected URL to contain '{expected_url}' but got '{current_url}'"
                logging.error(error_msg)
                log_form_validation_error(test_case_name, error_msg)
                raise AssertionError(error_msg)
            logging.info(f"Successfully logged in as {username}")
            
            # Perform additional validations if specified
            if 'additional_validations' in test_case:
                logging.info(f"Performing additional validations for test case: {test_case_name}")
                perform_additional_validations(page, test_case)
        else:
            # Check for error message
            if not error_element.is_visible():
                error_msg = f"[{test_case_name}] Expected error message not found"
                logging.error(error_msg)
                log_form_validation_error(test_case_name, error_msg)
                raise AssertionError(error_msg)
            
            error_message = error_element.text_content()
            logging.info(f"Received error message: {error_message}")
            log_form_validation_error(test_case_name, error_message)  # Always log error messages for error cases
            
            if 'expected_error_message' in test_case:
                expected_error = test_case['expected_error_message']
                if expected_error not in error_message:
                    error_msg = f"[{test_case_name}] Expected error message '{expected_error}' not found in '{error_message}'"
                    logging.error(error_msg)
                    log_form_validation_error(test_case_name, error_msg)
                    raise AssertionError(error_msg)
        
        logging.info(f"Test case completed: {test_case_name}")
        
    except Exception as e:
        logging.error(f"[{test_case_name}] Test failed: {str(e)}")
        capture_failure_screenshot(page, test_case_name)
        log_form_validation_error(test_case_name, str(e))
        raise

def run_all_tests():
    """Run all test cases"""
    # Set up logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('logs', exist_ok=True)
    
    # Clear previous validation errors log
    with open('logs/validation_errors.log', 'w') as f:
        f.write(f"=== Test Run Started at {timestamp} ===\n\n")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/test_run_{timestamp}.log'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Starting test suite")
    
    # Load test cases
    logging.info("Loading test cases from JSON file")
    test_cases = load_test_cases()
    logging.info(f"Loaded {len(test_cases)} test cases")
    
    # Launch browser
    logging.info("Launching browser")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Run each test case
            for test_case in test_cases:
                logging.info("\n" + "="*50)
                run_login_test(page, test_case)
                logging.info("="*50)
                
        except Exception as e:
            logging.error(f"Test suite failed: {str(e)}")
            raise
        finally:
            logging.info("Closing browser")
            browser.close()
    
    logging.info(f"Test suite completed. Log file: logs/test_run_{timestamp}.log")
    logging.info("Validation errors log: logs/validation_errors.log")

if __name__ == "__main__":
    # Ensure test_data directory exists
    os.makedirs('test_data', exist_ok=True)
    run_all_tests() 