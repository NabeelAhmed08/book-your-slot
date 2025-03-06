# SignUpGenius Automation Tool

An automation tool for monitoring and registering slots on SignUpGenius pages. Originally designed for UWM Food Pantry appointments but adaptable for any SignUpGenius registration.

## Features

- Automatic monitoring of web pages for new SignUpGenius links
- Scheduled checks at specified times
- Direct SignUpGenius URL support
- Configurable through command line or config file
- Headless or visible browser operation
- Automatic form filling and registration
- Logging system for tracking operations

## Prerequisites

- Python 3.6+
- Chrome browser installed
- Required Python packages (install via `pip install -r requirements.txt`):
  - selenium
  - webdriver-manager
  - schedule
  - python-dotenv
  - requests

## Setup

1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your settings using either:
   - Command line arguments
   - Config file (config.json)

## Configuration

You can configure the tool using either command line arguments or by updating the config.json file.

### Using Command Line

```bash
# Update configuration
python signupgenius_automator.py --configure --first-name "John" --last-name "Doe" --email "john@example.com"

# Show current configuration
python signupgenius_automator.py --show-config
```

### Using Config File

Create or modify `config.json`:
```json
{
    "user": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
    },
    "schedule": {
        "times": ["10:00", "12:00", "14:00", "16:00", "18:00"]
    },
    "urls": {
        "default": "https://www.example.com/signup-page"
    },
    "settings": {
        "headless": true,
        "stop_after_success": true
    }
}
```

## Usage

### Basic Usage

```bash
# Run immediately with current configuration
python signupgenius_automator.py --run-now

# Run with specific URL
python signupgenius_automator.py --run-now --url "https://www.signupgenius.com/go/example"

# Run in visible browser mode
python signupgenius_automator.py --run-now --visible
```

### Advanced Usage

```bash
# Skip URL checking for direct SignUpGenius links
python signupgenius_automator.py --run-now --url "https://www.signupgenius.com/go/example" --skip-check

# Schedule checks at specific times
python signupgenius_automator.py --times "10:00" "14:00" "18:00"

# Stop running automation
python signupgenius_automator.py --stop
```

### Command Line Arguments

- `--configure`: Update configuration
- `--show-config`: Display current configuration
- `--first-name`: Set first name
- `--last-name`: Set last name
- `--email`: Set email address
- `--headless`: Run in headless mode
- `--visible`: Run in visible browser mode
- `--stop-after-success`: Stop after successful registration
- `--run-now`: Run immediately
- `--url`: Specify URL to check
- `--skip-check`: Skip checking for signup links in URL
- `--times`: Set schedule times
- `--stop`: Stop running automation

## Logging

The tool maintains a log file (`signupgenius_automation.log`) with detailed information about its operations. Check this file for troubleshooting and verification of actions.

## Stopping the Automation

You can stop the automation in three ways:
1. Press Ctrl+C in the terminal
2. Create a file named `stop_automation.txt`
3. Run the script with `--stop` argument

## Contributing

Feel free to submit issues and enhancement requests.

## License

MIT License
