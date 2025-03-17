import logging
import schedule
import datetime
import time
import os
import threading
from typing import Optional

from .config_manager import load_config
from .browser_automation import check_for_new_link, register_for_slot
from .shared_state import stop_event, logger

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