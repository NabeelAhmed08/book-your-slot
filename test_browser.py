from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import sys
import os

def test_browser():
    print("Starting browser test...")
    
    try:
        # Load config to get the URL
        with open("config.json", 'r') as f:
            config = json.load(f)
        url = config["urls"]["default"]
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        print("Setting up Chrome driver...")
        # Get Chrome version first
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=chrome_options
            )
        except Exception as e:
            print(f"Error setting up ChromeDriver: {str(e)}")
            print("\nTrying alternative setup method...")
            # Alternative setup without version specification
            driver = webdriver.Chrome(options=chrome_options)
        
        print("Chrome driver setup successful!")
        print(f"Opening URL: {url}")
        driver.get(url)
        
        # Add a longer delay and progress indicator
        print("Browser will remain open for 30 seconds...")
        for i in range(30):
            sys.stdout.write(f"\rTime remaining: {30-i} seconds")
            sys.stdout.flush()
            time.sleep(1)
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nDebug information:")
        print(f"Python version: {sys.version}")
        print(f"Current working directory: {os.getcwd()}")
        if 'driver' in locals():
            print("Driver was initialized")
        else:
            print("Driver was not initialized")
    finally:
        if 'driver' in locals():
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    test_browser()
