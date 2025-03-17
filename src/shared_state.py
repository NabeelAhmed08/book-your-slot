import threading
import logging

# Shared stop event for clean termination
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
