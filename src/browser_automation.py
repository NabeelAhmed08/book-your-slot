import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import time

# Import stop_event and logger from shared_state module
from .shared_state import stop_event, logger

def setup_driver(headless=True):
    """
    Set up and configure Chrome WebDriver
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Add SSL error handling options
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        logger.info("Setting up Chrome driver...")
        try:
            # First attempt with ChromeDriverManager
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        except Exception as e:
            logger.warning(f"Standard setup failed: {str(e)}")
            logger.info("Trying alternative setup method...")
            # Alternative setup that worked in test_browser
            driver = webdriver.Chrome(options=chrome_options)
        
        # Set page load timeout
        #driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        logger.info("WebDriver setup successful")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to setup WebDriver: {str(e)}")
        raise


def check_for_new_link(url="https://uwm.edu/deanofstudents/assistance/food-pantry/", headless=True, skip_check=False):
    """
    Check for new SignUpGenius links on the UWM food pantry page.
    
    Args:
        url (str): The URL to check for new signup links
        headless (bool): Whether to run in headless mode
        skip_check (bool): If True, returns the URL directly if it's a SignUpGenius URL
        
    Returns:
        str or None: URL of the first matching signup link, or None if not found
    """
    # If skip_check is True and URL is a SignUpGenius URL, return it directly
    if skip_check and 'signupgenius.com' in url.lower():
        logger.info("Skipping link check - using provided SignUpGenius URL directly")
        return url

    driver = None
    try:
        logger.info(f"Starting link check for URL: {url}")
        
        # Set up the driver with headless mode for link checking
        driver = setup_driver(headless=headless)
        
        # Navigate to the page
        driver.get(url)
        logger.info("Successfully navigated to the target URL")
        
        # Get current date in required format - Windows compatible
        now = datetime.datetime.now()
        current_date = now.strftime("%#m/%#d/%y")  # Use # for Windows to remove leading zeros
        expected_text = f"{current_date} Food Pantry Appointment Sign Up"
        logger.info(f"Searching for link containing: {expected_text}")
        
        # Find all links on the page
        links = driver.find_elements(By.TAG_NAME, "a")
        
        # Search for matching link
        for link in links:
            try:
                link_text = link.text.strip()
                link_href = link.get_attribute('href')
                if  'signupgenius.com' in link_href.lower():
                    logger.info(f"Found matching signup link: {link_href}")
                    return link_href
            except Exception as e:
                logger.warning(f"Error processing a link: {str(e)}")
                continue
        
        logger.info("No matching signup link found")
        return None
        
    except TimeoutException:
        logger.error("Timeout while accessing the webpage")
        return None
    except NoSuchElementException:
        logger.error("Required elements not found on the webpage")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during link check: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
    # ...existing check_for_new_link code...

def register_for_slot(signup_url, first_name, last_name, email, headless=False):
    """
    Register for an available slot on SignUpGenius using specific element locators.
    """
    driver = None
    try:
        logger.info(f"Starting registration process for {email}")
        
        # Use visible browser for registration unless headless is specified
        driver = setup_driver(headless=headless)
        driver.maximize_window()  # Ensure window is maximized
        
        # Navigate to the signup page
        logger.info(f"Navigating to signup URL: {signup_url}")
        driver.get(signup_url)
        
        # Click the initial signup button using exact xpath
        logger.info("Clicking initial signup button")
        wait = WebDriverWait(driver, 5)
        # Find all signup buttons and click the second one (index 1)
        signup_buttons = wait.until(
            EC.presence_of_all_elements_located((
            By.XPATH, "//div/div/div/signup-button/button"
            ))
        )
        
        if not signup_buttons:
            logger.error("No signup buttons found on page")
            stop_event.set()  # Set stop event to exit automation
            return False

        # Try each signup button until finding one that's enabled
        button_clicked = False
        for button in signup_buttons:
            try:
                if button.is_enabled() and button.is_displayed():
                    logger.info("Found enabled signup button")
                    wait.until(EC.element_to_be_clickable(button)).click()
                    button_clicked = True
                    break
            except Exception as e:
                logger.debug(f"Button not clickable, trying next one: {str(e)}")
                continue
                
        if not button_clicked:
            logger.error("No enabled signup buttons found - slots may be full")
            stop_event.set()  # Set stop event to exit automation
            return False

        # Click the confirmation button
        logger.info("Clicking confirmation button")
        confirm_button = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, "//div[@id='signupContainerId']/div[4]/div/button"
            ))
        )
        confirm_button.click()
        
        # Fill in the registration form using ID selectors
        logger.info("Filling registration form")
        
        # First Name
        firstname_field = wait.until(EC.presence_of_element_located((By.ID, "firstname")))
        firstname_field.click()
        firstname_field.clear()
        firstname_field.send_keys(first_name)
        
        # Last Name
        lastname_field = wait.until(EC.presence_of_element_located((By.ID, "lastname")))
        lastname_field.click()
        lastname_field.clear()
        lastname_field.send_keys(last_name)
        
        # Email
        email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_field.click()
        email_field.clear()
        email_field.send_keys(email)
        
        # Submit the form
        logger.info("Submitting registration form")
        submit_button = wait.until(
            EC.element_to_be_clickable((By.NAME, "btnSignUp"))
        )
        submit_button.click()
        
        # Wait for success confirmation
        time.sleep(2)  # Brief pause to ensure form submission
        logger.info(f"Successfully registered {email} for slot")
        return True
        
    except TimeoutException as e:
        logger.error(f"Timeout while registering: {str(e)}")
        stop_event.set()  # Set stop event to exit automation
        return False
    except NoSuchElementException as e:
        logger.error(f"Required element not found: {str(e)}")
        stop_event.set()  # Set stop event to exit automation
        return False
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        stop_event.set()  # Set stop event to exit automation
        return False
    finally:
        if driver:
            try:
                if not headless:
                    time.sleep(2)  # Brief pause to see result if visible
                driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")