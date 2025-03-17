import logging
import schedule
import datetime
import time
from datetime import datetime, timedelta
from typing import Optional
import threading

from .config_manager import load_config
from .browser_automation import check_for_new_link, register_for_slot
from .shared_state import stop_event, logger

def job(first_name: str, last_name: str, email: str, url: Optional[str] = None, 
        skip_check: bool = False, headless: Optional[bool] = None) -> None:
    """
    Main job function that checks for new links and attempts registration.
    """
    try:
        if stop_event.is_set():
            return
            
        logger.info("Starting scheduled job execution")
        config = load_config()
        
        # Use provided headless setting or fall back to config
        use_headless = headless if headless is not None else config["settings"]["headless"]
        
        signup_link = None
        if skip_check and url and 'signupgenius.com' in url.lower():
            logger.info("Using provided SignUpGenius URL directly")
            signup_link = url
        else:
            check_url = url or config["urls"]["default"]
            signup_link = check_for_new_link(
                check_url, 
                headless=use_headless,
                skip_check=skip_check
            )

        if signup_link:
            success = register_for_slot(
                signup_url=signup_link,
                first_name=first_name,
                last_name=last_name,
                email=email,
                headless=use_headless
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

class ScheduledCheck:
    def __init__(self):
        self.is_checking = False
        self.check_thread = None
        self.last_check_time = None
        self.check_lock = threading.Lock()

    def start_checking(self, config: dict, first_name: str, last_name: str, email: str):
        """Start checking for slots within the configured time window"""
        with self.check_lock:
            if self.is_checking:
                return
            
            self.is_checking = True
            current_time = datetime.now().time()
            start_time = datetime.strptime(config["schedule"]["start_time"], "%H:%M").time()
            end_time = datetime.strptime(config["schedule"]["end_time"], "%H:%M").time()
            check_interval = config["schedule"].get("check_interval", 10)  # Default to 10 if not set
            
            if not (start_time <= current_time <= end_time):
                logger.info("Outside checking window, waiting for next scheduled run")
                self.is_checking = False
                return

            def check_loop():
                while self.is_checking and not stop_event.is_set():
                    current_time = datetime.now().time()
                    if current_time > end_time:
                        logger.info("Reached end time, stopping checks")
                        self.stop_checking()
                        break

                    try:
                        # Attempt to find and register for a slot
                        job(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            skip_check=config["settings"]["skip_check"],
                            headless=config["settings"]["headless"]
                        )
                            
                        # Wait for the configured interval
                        time.sleep(check_interval * 60)
                    except Exception as e:
                        logger.error(f"Error in check loop: {str(e)}")
                        self.stop_checking()
                        break

            self.check_thread = threading.Thread(target=check_loop)
            self.check_thread.start()

    def stop_checking(self):
        """Stop the current checking cycle"""
        with self.check_lock:
            self.is_checking = False
            if self.check_thread:
                self.check_thread.join(timeout=1)
                self.check_thread = None

    def _attempt_registration(self, config: dict, first_name: str, last_name: str, email: str) -> bool:
        """Attempt to find and register for a slot"""
        return job(
            first_name=first_name,
            last_name=last_name,
            email=email,
            skip_check=config["settings"]["skip_check"],
            headless=config["settings"]["headless"]
        )

def scheduler_thread(first_name: str, last_name: str, email: str, times: Optional[list[str]] = None, skip_check: bool = False):
    """Main scheduler thread function"""
    config = load_config()
    checker = ScheduledCheck()
    
    def scheduled_job():
        """Job to be run on the scheduled day"""
        logger.info("Starting scheduled check window")
        checker.start_checking(config, first_name, last_name, email)

    # Schedule for the configured day of the week
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day = day_names[config["schedule"]["day_of_week"]]
    
    # Schedule the job for the configured day and start time
    getattr(schedule.every(), day).at(config["schedule"]["start_time"]).do(scheduled_job)
    logger.info(f"Scheduled weekly check for {day} at {config['schedule']['start_time']}")

    # Main loop
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

    # Ensure checking stops when main loop exits
    checker.stop_checking()
    logger.info("Scheduler thread exiting")