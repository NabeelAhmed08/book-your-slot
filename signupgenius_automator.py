import logging
import os
import argparse
import json
import threading
import signal
import sys
import time
from typing import Optional

# Import from local modules
from src.config_manager import load_config, update_config
from src.scheduler import job, scheduler_thread
from src.shared_state import stop_event, logger


def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Received termination signal, shutting down gracefully...")
    stop_event.set()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)




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