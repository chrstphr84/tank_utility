***REMOVED*** Notification Script

This script interacts with the Tank Utility API to read the status of a propane tank using the original WiFi Propane Tank Level Monitor (prev. Tank Utility, now Generac.) and sends notifications based on certain conditions, such as battery level and tank level. 

It has only been tested with the original Tank Utility monitor (prior to Generac).

This script is for personal use and has no official affliation with Tank Utility or Generac.

## Features

- Fetches device information from the Tank Utility API.
- Monitors battery status and propane level.
- Sends notifications when the battery level is low or critical.
- Sends notifications when the tank's propane level drops below certain thresholds (50%, 40%, 30%).

## Requirements

- Python 3.x
- `requests` library
- Uses the Pushover app/service to send push notifications.  https://apps.apple.com/us/app/pushover-notifications/id506088175
- `pushover` library


## Installation

1. Clone the repository or download the script.
2. Install the required libraries using pip:

    ```
    pip install requests pushover
    ```

## Usage

1. Replace `your_api_token_here` with your Tank Utility API token and credentials in constants.py.  They can alternatively be hardcoded at your own risk.
2. Run the script:

    ```
    python tank.py
    ```

## Functions

### `get_devices(token)`

Fetches the list of devices associated with the given API token.

### `get_device_data(token, device_id)`

Fetches the data for a specific device using the device ID and API token.

### `push_tank_level()`

Sends a push notification if the tank level is below 30%.

### `push_battery_status()`

Sends a push notification if the battery level is critical.

## Message Dictionary

The `message_dict` dictionary contains predefined messages for different conditions:

- `status`: Current status of the tank.
- `battery_low`: Message for low battery level.
- `battery_critical`: Message for critical battery level.
- `level_below_50`: Message for tank level below 50%.
- `level_below_40`: Message for tank level below 40%.
- `level_below_30`: Message for tank level below 30%.

## Example

Here is an example of how the script sends notifications based on the tank level and battery status:

```python
def push_tank_level():
    if lastReading <= 30.00:
        message = pushover.push(message_dict["level_below_30"])
        message.notification()

def push_battery_status():
    if battery_critical:
        message = pushover.push(message_dict["battery_critical"])
        message.notification()