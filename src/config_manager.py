import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

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