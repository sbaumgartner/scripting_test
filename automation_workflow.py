from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from datetime import timedelta
from playwright.sync_api import sync_playwright, expect
import json
import os
from datetime import datetime
from models.product_search import ProductSearchConfig
from decimal import Decimal

@task
def setup_environment():
    """Set up the test environment"""
    logger = get_run_logger()
    
    # Create required directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('screenshots', exist_ok=True)
    
    logger.info("Environment setup completed")
    return True

@task(retries=3, retry_delay_seconds=5)
def load_and_validate_config():
    """Load and validate the test configuration"""
    logger = get_run_logger()
    
    try:
        with open('test_data/product_search_config.json', 'r') as file:
            config_data = json.load(file)
            config = ProductSearchConfig(**config_data)
            logger.info("Configuration validated successfully")
            return config
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise

@task
def create_browser_session():
    """Create a new browser session"""
    logger = get_run_logger()
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        logger.info("Browser session created successfully")
        return playwright, browser, page
    except Exception as e:
        logger.error(f"Failed to create browser session: {str(e)}")
        raise

@task
def login_to_website(page, username="standard_user", password="secret_sauce"):
    """Login to the website"""
    logger = get_run_logger()
    
    try:
        logger.info("Navigating to website")
        page.goto('https://www.saucedemo.com/')
        
        logger.info("Filling login form")
        page.fill('#user-name', username)
        page.fill('#password', password)
        
        logger.info("Clicking login button")
        page.click('#login-button')
        
        # Wait for successful login with better error handling
        try:
            page.wait_for_selector('.inventory_item', timeout=4000)  # Increased timeout to 4 seconds
            logger.info("Login successful")
            return True
        except Exception as e:
            logger.error("Login failed - inventory items not found")
            raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise

@task
def find_product(page, product_name):
    """Find a specific product on the page"""
    logger = get_run_logger()
    
    try:
        logger.info(f"Searching for product: {product_name}")
        # Wait for products to be visible
        page.wait_for_selector('.inventory_item', timeout=10000)
        products = page.locator('.inventory_item').all()
        
        for product in products:
            current_name = product.locator('.inventory_item_name').text_content()
            if current_name.strip() == product_name:
                logger.info(f"Product found: {product_name}")
                return product
        
        raise ValueError(f"Product '{product_name}' not found")
    except Exception as e:
        logger.error(f"Product search failed: {str(e)}")
        raise

@task
def verify_product_details(page, product, expected_price, expected_description):
    """Verify product price and description"""
    logger = get_run_logger()
    
    try:
        # Verify price
        price_text = product.locator('.inventory_item_price').text_content()
        actual_price = Decimal(price_text.replace('$', ''))
        
        if actual_price != expected_price:
            raise ValueError(f"Price mismatch. Expected: ${expected_price}, Got: ${actual_price}")
        
        # Click to view details and wait for navigation
        logger.info("Clicking product to view details")
        product.click()
        
        # Wait for the details page to load
        try:
            # First wait for the URL to change
            page.wait_for_url("**/inventory-item.html", timeout=10000)
            # Then wait for the description element
            page.wait_for_selector('.inventory_details_desc', timeout=10000)
            
            # Verify description
            actual_description = page.locator('.inventory_details_desc').text_content()
            if actual_description.strip() != expected_description:
                raise ValueError(f"Description mismatch.\nExpected: {expected_description}\nGot: {actual_description}")
            
            logger.info("Product details verified successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load product details page: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Product verification failed: {str(e)}")
        raise

@task
def capture_screenshot(page, test_name):
    """Capture screenshot of the current page"""
    logger = get_run_logger()
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f'screenshots/{test_name}_{timestamp}.png'
        page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot captured: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logger.error(f"Screenshot capture failed: {str(e)}")
        raise

@task
def cleanup_browser_session(playwright, browser):
    """Clean up browser resources"""
    logger = get_run_logger()
    try:
        browser.close()
        playwright.stop()
        logger.info("Browser session cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to clean up browser session: {str(e)}")
        raise

@flow(name="Product Search Automation")
def product_search_workflow():
    """Main workflow for product search automation"""
    logger = get_run_logger()
    
    try:
        # Setup environment
        setup_environment()
        
        # Load and validate configuration
        config = load_and_validate_config()
        search_config = config.product_search
        
        # Create browser session
        playwright, browser, page = create_browser_session()
        
        try:
            # Login to website
            login_to_website(page)
            
            # Find product
            product = find_product(page, search_config.name)
            
            # Verify product details
            verify_product_details(
                page, 
                product, 
                search_config.expected_price, 
                search_config.expected_description
            )
            
            # Capture success screenshot
            capture_screenshot(page, "success")
            
            logger.info("Workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            # Capture failure screenshot
            capture_screenshot(page, "failure")
            raise
        finally:
            # Clean up browser session
            cleanup_browser_session(playwright, browser)
            
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        raise

if __name__ == "__main__":
    product_search_workflow() 