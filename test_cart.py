import json
import logging
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import re

def load_test_cases():
    """Load test cases from JSON file"""
    with open('test_data/cart_test_cases.json', 'r') as f:
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
    """Capture screenshot on test failure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs('screenshots', exist_ok=True)
    screenshot_path = f'screenshots/failure_{test_case_name}_{timestamp}.png'
    page.screenshot(path=screenshot_path)
    logging.info(f"Screenshot captured: {screenshot_path}")

def add_items_to_cart(page, items):
    """Add items to cart and verify their prices"""
    total_price = 0
    for item in items:
        # Find the item container by name using Playwright's :has and :has-text
        item_container = page.locator(f'.inventory_item:has(.inventory_item_name:has-text("{item["name"]}"))').first
        if not item_container:
            raise AssertionError(f"Item not found: {item['name']}")
        
        # Get the price from within the container
        price_element = item_container.locator('.inventory_item_price')
        price_text = price_element.text_content()
        actual_price = float(price_text.replace('$', ''))
        
        # Verify price
        if actual_price != item['expected_price']:
            error_msg = f"Price mismatch for {item['name']}: expected ${item['expected_price']}, got ${actual_price}"
            logging.error(error_msg)
            log_form_validation_error("price_verification", error_msg)
            raise AssertionError(error_msg)
        
        # Add to cart
        add_to_cart_button = item_container.locator('.btn_inventory')
        add_to_cart_button.click()
        total_price += actual_price
        
        # Wait for cart badge to update
        page.wait_for_timeout(500)  # Small delay to ensure cart updates
    
    return total_price

def verify_cart(page, expected_count, expected_total):
    """Verify cart contents and (if on summary page) total price"""
    # On the cart page, check item count
    cart_items = page.locator('.cart_item').all()
    assert len(cart_items) == expected_count, f"Cart should have {expected_count} items, found {len(cart_items)}"
    logging.info(f"Verified cart contains {len(cart_items)} items")

    # Optionally, check item prices on the cart page
    cart_prices = [float(item.locator('.inventory_item_price').text_content().replace('$', '')) for item in cart_items]
    total_cart_price = sum(cart_prices)
    assert abs(total_cart_price - expected_total) < 0.01, f"Cart total mismatch: expected ${expected_total}, got ${total_cart_price}"
    logging.info(f"Verified cart total price: ${total_cart_price:.2f}")

    # If on the summary page, check the summary subtotal
    if page.url.endswith('/checkout-step-two.html'):
        total_element = page.locator('.summary_subtotal_label')
        total_text = total_element.text_content()
        subtotal = float(total_text.replace('Item total: $', ''))
        assert abs(subtotal - expected_total) < 0.01, f"Summary subtotal mismatch: expected ${expected_total}, got ${subtotal}"
        logging.info(f"Verified summary subtotal: ${subtotal:.2f}")

def normalize_text(text):
    # Lowercase, remove punctuation, and strip whitespace
    return re.sub(r'[^a-z0-9]', '', text.lower())

def perform_checkout(page, test_case):
    """Perform checkout process"""
    # Click checkout button
    page.click('#checkout')
    
    # Fill checkout information
    if 'checkout_info' in test_case:
        info = test_case['checkout_info']
        page.fill('#first-name', info.get('first_name', 'John'))
        page.fill('#last-name', info.get('last_name', 'Doe'))
        page.fill('#postal-code', info.get('postal_code', '12345'))
    else:
        page.fill('#first-name', 'John')
        page.fill('#last-name', 'Doe')
        page.fill('#postal-code', '12345')
    
    # Continue to next step
    page.click('#continue')
    
    # Check for errors
    error_element = page.locator('[data-test="error"]')
    if error_element.is_visible():
        error_message = error_element.text_content()
        logging.warning(f"Checkout error: {error_message}")
        log_form_validation_error(test_case['name'], error_message)
        if test_case['expected_result'] == 'error':
            assert test_case['expected_error_message'] in error_message, \
                f"Expected error message '{test_case['expected_error_message']}' not found in '{error_message}'"
            return False
        raise AssertionError(f"Unexpected checkout error: {error_message}")
    
    # Complete checkout
    page.click('#finish')
    
    # Wait for confirmation page
    page.wait_for_url(lambda url: url.endswith('/checkout-complete.html'), timeout=10000)
    complete_header = page.locator('.complete-header')
    complete_header.wait_for(state='visible', timeout=5000)

    # Log the actual header text for debugging
    header_text = complete_header.text_content()
    logging.info(f"Complete header text: '{header_text}'")

    # Verify completion
    if test_case['expected_result'] == 'success':
        assert page.url.endswith('/checkout-complete.html'), "Should be on checkout complete page"
        assert complete_header.is_visible(), "Completion header should be visible"
        expected = normalize_text('THANK YOU FOR YOUR ORDER')
        actual = normalize_text(header_text)
        assert expected in actual, f"Should show thank you message, got: '{header_text}'"
    
    return True

def run_cart_test(page, test_case):
    """Run a single cart/checkout test case"""
    test_case_name = test_case['name']
    username = test_case['username']
    password = test_case['password']
    expected_result = test_case['expected_result']
    expected_error_message = test_case.get('expected_error_message', None)

    logging.info(f"Starting test case: {test_case_name}")
    try:
        # Login
        logging.info("Navigating to website")
        page.goto('https://www.saucedemo.com/')
        logging.info("Filling login form")
        page.fill('#user-name', username)
        page.fill('#password', password)
        logging.info("Clicking login button")
        page.click('#login-button')
        page.wait_for_load_state('networkidle')

        # Add items to cart
        logging.info("Adding items to cart")
        total_price = add_items_to_cart(page, test_case['items'])
        logging.info(f"Total price: ${total_price:.2f}")

        # Navigate to cart page before verifying cart
        page.click('.shopping_cart_link')
        page.wait_for_load_state('networkidle')

        # Verify cart contents
        verify_cart(page, len(test_case['items']), total_price)

        # Perform checkout
        logging.info("Starting checkout process")
        checkout_success = perform_checkout(page, test_case)
        
        if test_case['expected_result'] == 'success':
            assert checkout_success, "Checkout should succeed"
        else:
            assert not checkout_success, "Checkout should fail"
        
        logging.info(f"Test case completed: {test_case_name}")
        
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        capture_failure_screenshot(page, test_case_name)
        log_form_validation_error(test_case_name, str(e))
        raise

def run_all_tests():
    """Run all test cases"""
    logging.info("Starting cart tests")
    
    try:
        test_cases = load_test_cases()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            for test_case in test_cases:
                run_cart_test(page, test_case)
            
            browser.close()
        
        logging.info("All cart tests completed successfully")
        return True
    except Exception as e:
        logging.error(f"Cart tests failed: {str(e)}")
        raise

if __name__ == '__main__':
    run_all_tests() 