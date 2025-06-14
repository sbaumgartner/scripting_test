import unittest
import logging
import os
from datetime import datetime
import test_login
import test_product_data
import test_cart
import traceback
from prefect import flow, task, get_run_logger
from prefect.logging import get_logger

def setup_logging():
    """Set up logging configuration for the test suite"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create screenshots directory if it doesn't exist
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')
    
    # Clear validation errors log at start of test run
    with open('logs/validation_errors.log', 'w') as f:
        f.write(f"=== Test Run Started at {datetime.now()} ===\n\n")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # Create handlers
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(f'logs/test_run_{timestamp}.log')
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure Prefect logger
    prefect_logger = get_logger()
    prefect_logger.setLevel(logging.INFO)
    
    return root_logger

@task(retries=3, retry_delay_seconds=5)
def initialize_test_run():
    """Initialize the test run environment"""
    logger = get_run_logger()
    logger.info("Initializing test run environment")
    setup_logging()
    logger.info("Test run environment initialized")
    return True

@task(retries=2, retry_delay_seconds=5)
def run_login_tests():
    """Run login test suite"""
    logger = get_run_logger()
    logger.info("\n=== Running Login Tests ===")
    test_login.run_all_tests()
    return True

@task(retries=2, retry_delay_seconds=5)
def run_product_data_tests():
    """Run product data test suite"""
    logger = get_run_logger()
    logger.info("\n=== Running Product Data Tests ===")
    test_product_data.run_all_tests()
    return True

@task(retries=2, retry_delay_seconds=5)
def run_cart_tests():
    """Run cart test suite"""
    logger = get_run_logger()
    logger.info("\n=== Running Cart Tests ===")
    test_cart.run_all_tests()
    return True

@flow(name="Sauce Demo Test Suite")
def run_tests():
    """Run all test suites in sequence"""
    logger = get_run_logger()
    logger.info("Starting test suite execution")
    failures = []
    
    try:
        # Run login tests
        run_login_tests()
    except Exception as e:
        logger.error(f"Login tests failed: {str(e)}")
        failures.append(("Login Tests", str(e), traceback.format_exc()))
    
    try:
        # Run product data tests
        run_product_data_tests()
    except Exception as e:
        logger.error(f"Product data tests failed: {str(e)}")
        failures.append(("Product Data Tests", str(e), traceback.format_exc()))
    
    try:
        # Run cart tests
        run_cart_tests()
    except Exception as e:
        logger.error(f"Cart tests failed: {str(e)}")
        failures.append(("Cart Tests", str(e), traceback.format_exc()))
    
    # Log summary
    logger.info("\n=== Test Run Summary ===")
    if failures:
        logger.error(f"Test suite completed with {len(failures)} failures:")
        for suite_name, error, stack_trace in failures:
            logger.error(f"\n{suite_name} failed:")
            logger.error(f"Error: {error}")
            logger.error(f"Stack trace:\n{stack_trace}")
        return False
    else:
        logger.info("All test suites completed successfully")
        return True

if __name__ == '__main__':
    initialize_test_run()
    success = run_tests()
    logging.info(f"Test suite execution {'completed successfully' if success else 'failed'}")
    exit(0 if success else 1) 