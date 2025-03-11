from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import schedule
import time
import datetime
import logging
import os
import argparse
import json
import threading
import signal
import sys
from typing import Optional, Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "user": {
        "first_name": "",
        "last_name": "",
        "email": ""
    },
    "schedule": {
        "times": ["10:00", "12:00", "14:00", "16:00", "18:00"]
    },
    "urls": {
        "default": "https://uwm.edu/food-pantry/"
    },
    "settings": {
        "headless": False,
        "stop_after_success": True,
        "skip_check": False
    }
}

# Stop event for clean termination
stop_event = threading.Event()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signupgenius_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Received termination signal, shutting down gracefully...")
    stop_event.set()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json file.
    Creates default config if file doesn't exist.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config_path = "config.json"
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded successfully")
                return config
        else:
            logger.info("No configuration file found, creating default")
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
            
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration to config.json file.
    
    Args:
        config (Dict[str, Any]): Configuration to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open("config.json", 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("Configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False

def update_config(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    times: Optional[list[str]] = None,
    default_url: Optional[str] = None,
    headless: Optional[bool] = None,
    stop_after_success: Optional[bool] = None,
    skip_check: Optional[bool] = None
) -> bool:
    """
    Update specific fields in the configuration.
    
    Args:
        first_name (Optional[str]): User's first name
        last_name (Optional[str]): User's last name
        email (Optional[str]): User's email
        times (Optional[list[str]]): List of schedule times
        default_url (Optional[str]): Default URL to check
        headless (Optional[bool]): Run browsers in headless mode
        stop_after_success (Optional[bool]): Stop automation after successful registration
        skip_check (Optional[bool]): Skip URL check for direct SignUpGenius URLs
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        config = load_config()
        
        if first_name is not None:
            config["user"]["first_name"] = first_name
        if last_name is not None:
            config["user"]["last_name"] = last_name
        if email is not None:
            config["user"]["email"] = email
        if times is not None:
            config["schedule"]["times"] = times
        if default_url is not None:
            config["urls"]["default"] = default_url
        if headless is not None:
            config["settings"]["headless"] = headless
        if stop_after_success is not None:
            config["settings"]["stop_after_success"] = stop_after_success
        if skip_check is not None:
            config["settings"]["skip_check"] = skip_check
            
        return save_config(config)
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        return False

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

def check_for_new_link(url="https://uwm.edu/food-pantry/", headless=True, skip_check=False):
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

def job(first_name: str, last_name: str, email: str, url: Optional[str] = None, 
        skip_check: bool = False, headless: Optional[bool] = None) -> None:
    """
    Main job function that checks for new links and attempts registration.
    
    Args:
        first_name (str): User's first name
        last_name (str): User's last name
        email (str): User's email address
        url (Optional[str]): Optional specific URL to check or direct SignUpGenius URL
        skip_check (bool): Skip checking for signup links if True
        headless (Optional[bool]): Override config headless setting
    """
    try:
        if stop_event.is_set():
            return
            
        logger.info("Starting scheduled job execution")
        config = load_config()
        
        # Use provided headless setting or fall back to config
        use_headless = headless if headless is not None else config["settings"]["headless"]
        
        signup_link = None
        if url and 'signupgenius.com' in url.lower():
            logger.info("Using provided SignUpGenius URL directly")
            signup_link = url
        else:
            check_url = url or config["urls"]["default"]
            signup_link = check_for_new_link(
                check_url, 
                headless=use_headless,  # Use determined headless setting
                skip_check=skip_check
            )
        
        if signup_link:
            logger.info(f"Found new signup link: {signup_link}")
            
            # Attempt registration with determined headless setting
            success = register_for_slot(
                signup_url=signup_link,
                first_name=first_name,
                last_name=last_name,
                email=email,
                headless=use_headless  # Use determined headless setting
            )
            
            if success:
                logger.info("Successfully registered for slot!")
                if config["settings"]["stop_after_success"]:
                    logger.info("Stopping automation after successful registration")
                    stop_event.set()
            else:
                logger.error("Failed to register for slot")
        else:
            logger.info("No new signup link found")
            
    except Exception as e:
        logger.error(f"Error in job execution: {str(e)}")

def scheduler_thread(first_name: str, last_name: str, email: str, times: Optional[list[str]] = None, skip_check: bool = False):
    """
    Main scheduler thread function that schedules jobs for configured times on Mondays
    """
    config = load_config()
    scheduled_times = times or config["schedule"]["times"]
    
    # Run once immediately if it's Monday and between 9:20 AM and 10:00 AM
    now = datetime.datetime.now()
    if now.weekday() == 0:  # Monday
        current_time = now.time()
        start_time = datetime.time(9, 20)
        end_time = datetime.time(10, 0)
        
        if start_time <= current_time <= end_time:
            logger.info("Running initial check as we're in the registration window...")
            job(first_name, last_name, email, skip_check=skip_check)
    
    # Schedule jobs for all configured times
    for time_str in scheduled_times:
        schedule.every().monday.at(time_str).do(
            job, first_name=first_name, last_name=last_name, email=email, skip_check=skip_check
        )
        logger.info(f"Scheduled job for Mondays at {time_str}")
    
    # Create a stop file check
    stop_file = "stop_automation.txt"
    
    # Main loop with multiple exit conditions
    while not stop_event.is_set():
        schedule.run_pending()
        
        # Check for stop file as backup exit mechanism
        if os.path.exists(stop_file):
            logger.info("Stop file detected, shutting down...")
            stop_event.set()
            try:
                os.remove(stop_file)
            except:
                pass
            break
            
        time.sleep(1)
    
    logger.info("Scheduler thread exiting")

def main():
    """Main function handling command line arguments and scheduling."""
    parser = argparse.ArgumentParser(description="SignUpGenius Automation Tool")
    
    # Configuration management arguments
    parser.add_argument("--configure", action="store_true", help="Update configuration")
    parser.add_argument("--show-config", action="store_true", help="Display current configuration")
    
    # User information arguments
    parser.add_argument("--first-name", help="Your first name")
    parser.add_argument("--last-name", help="Your last name")
    parser.add_argument("--email", help="Your email address")
    
    # Settings arguments
    parser.add_argument("--headless", dest="headless", action="store_true", help="Run browsers in headless mode")
    parser.add_argument("--visible", dest="headless", action="store_false", help="Run browsers in visible mode")
    parser.add_argument("--stop-after-success", action="store_true", help="Stop after successful registration")
    
    # Execution arguments
    parser.add_argument("--run-now", action="store_true", help="Run the job immediately")
    parser.add_argument("--url", help="Specific SignUpGenius URL to check")
    parser.add_argument("--skip-check", action="store_true", help="Skip checking for signup links in URL")
    parser.add_argument(
        "--times",
        nargs="+",
        help="Times to run on Mondays (24-hour format, e.g., 14:00)"
    )
    
    # Action arguments
    parser.add_argument("--stop", action="store_true", help="Stop running automation")
    
    parser.set_defaults(headless=None)
    args = parser.parse_args()
    
    # Handle stop request
    if args.stop:
        with open("stop_automation.txt", "w") as f:
            f.write("stop")
        print("Stop request sent. Automation will stop shortly.")
        return
    
    # Load configuration
    config = load_config()
    
    # Handle configuration display
    if args.show_config:
        print("\nCurrent Configuration:")
        print(json.dumps(config, indent=4))
        return
    
    # Handle configuration updates
    if args.configure:
        update_config(
            first_name=args.first_name,
            last_name=args.last_name,
            email=args.email,
            times=args.times,
            default_url=args.url,
            headless=args.headless,
            stop_after_success=args.stop_after_success if args.stop_after_success is not None else None
        )
        print("\nConfiguration updated successfully!")
        return
    
    # Get user information from config if not provided
    first_name = args.first_name or config["user"]["first_name"]
    last_name = args.last_name or config["user"]["last_name"]
    email = args.email or config["user"]["email"]
    
    # Validate required information
    if not all([first_name, last_name, email]):
        print("\nError: Missing required user information!")
        print("Please either provide information via command line arguments or update the configuration.")
        print("Use --configure to update configuration or --show-config to view current settings.")
        return
    
    # Update headless setting if specified
    if args.headless is not None:
        update_config(headless=args.headless)
        config = load_config()  # Reload with new setting
    
    # Log startup information
    logger.info("SignUpGenius Automation Started")
    logger.info(f"User: {first_name} {last_name} ({email})")
    
    try:
        # Run immediately if requested
        if args.run_now:
            logger.info("Running job immediately")
            job(first_name, last_name, email, args.url, skip_check=args.skip_check)
            if not stop_event.is_set():
                print("\nImmediate job completed. Starting scheduler...")
            else:
                print("\nRegistration successful! Automation completed.")
                return
        
        # Start scheduler in a daemon thread
        if not stop_event.is_set():
            scheduler = threading.Thread(
                target=scheduler_thread,
                args=(first_name, last_name, email, args.times),
                kwargs={"skip_check": args.skip_check},
                daemon=True
            )
            scheduler.start()
            
            print("\nAutomation running in background. Press Ctrl+C to stop.")
            print("You can also stop the automation by creating a file named 'stop_automation.txt'")
            print("or by running this script with the --stop argument.")
            
            # Main thread wait for stop event
            while not stop_event.is_set():
                time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        stop_event.set()
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {str(e)}")
        stop_event.set()
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()