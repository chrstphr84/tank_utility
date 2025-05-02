#!/usr/bin/env python3

import json
import os
import sys
import logging
from datetime import datetime
import requests

import pushover
import constants


class TankUtilityMonitor:
    def __init__(self):
        self.token = None
        self.device_id = None
        self.device_data = None
        self.setup_logging()

        # Configure thresholds that trigger notifications
        self.tank_level_thresholds = {
            30: "level_below_30",
            40: "level_below_40",
            50: "level_below_50"
        }

    def setup_logging(self):
        """Configure logging to console only, file logging will be handled separately"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("tank_utility")

    def validate_environment(self):
        """Verify that all required environment variables are set"""
        # Create a mapping between environment variable names and their attribute names in constants
        env_var_mapping = {
            "TANKUTILITY_USER": "tankUtilityUser",
            "TANKUTILITY_PW": "tankUtilityPw",
            "PUSHOVER_USER": "pushOverUser",
            "PUSHOVER_TOKEN": "pushOverToken"
        }

        missing = [env_var for env_var, attr_name in env_var_mapping.items()
                   if not getattr(constants, attr_name)]

        if missing:
            self.logger.error(f"Missing environment variables: {', '.join(missing)}")
            return False
        return True

    def get_auth_token(self):
        """Get authentication token from Tank Utility API"""
        try:
            response = requests.get(
                "https://data.tankutility.com/api/getToken",
                auth=(constants.tankUtilityUser, constants.tankUtilityPw),
                timeout=10  # Add timeout to prevent hanging indefinitely
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("token")
            if not self.token:
                self.logger.error("Failed to get valid token from API")
                return False
            return True

        except requests.exceptions.HTTPError as err:
            data_err = json.loads(err.response.text) if err.response.text else {"statusCode": "unknown",
                                                                                "error": "No error details"}
            self.logger.error(
                f"HTTP ERROR: {data_err.get('statusCode', 'unknown')} {err.response.status_code}"
            )
            self.logger.error(f"DETAIL: {data_err.get('error', 'No error details')}")
            return False

        except requests.exceptions.ConnectionError as conn_err:
            self.logger.error(f"NETWORK CONNECTION ERROR: {conn_err}")
            return False

        except requests.exceptions.Timeout:
            self.logger.error("Request timed out while connecting to Tank Utility API")
            return False

        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request error: {req_err}")
            return False

        except json.JSONDecodeError:
            self.logger.error("Failed to parse API response as JSON")
            return False

    def get_devices(self):
        """Get list of devices from Tank Utility API"""
        try:
            response = requests.get(
                f"https://data.tankutility.com/api/devices?token={self.token}",
                timeout=10
            )
            response.raise_for_status()
            device_data = response.json()

            self.device_id = device_data.get("devices", [])
            if not self.device_id:
                self.logger.error("No devices found")
                return False

            return True

        except (requests.exceptions.RequestException, json.JSONDecodeError) as err:
            self.logger.error(f"Error getting devices: {err}")
            return False

    def get_device_data(self):
        """Get data for the first device"""
        if not self.device_id:
            self.logger.error("No device ID available")
            return False

        try:
            response = requests.get(
                f"https://data.tankutility.com/api/devices/{self.device_id[0]}?token={self.token}",
                timeout=10
            )
            response.raise_for_status()
            self.device_data = response.json()
            return True

        except (requests.exceptions.RequestException, json.JSONDecodeError) as err:
            self.logger.error(f"Error getting device data: {err}")
            return False

    def process_device_data(self):
        """Process the device data and return status information"""
        if not self.device_data:
            return None

        device_info = {}

        # Device information
        device = self.device_data.get("device", {})
        device_info["name"] = device.get("name", "Unknown")
        device_info["battery_critical"] = device.get("battery_crit", False)
        device_info["battery_warning"] = device.get("battery_warn", False)
        device_info["average_consumption"] = device.get("average_consumption", 0)

        # Last reading information
        last_reading = device.get("lastReading", {})
        device_info["temperature"] = last_reading.get("temperature")

        # Time
        timestamp = last_reading.get("time")
        if timestamp:
            device_info["timestamp"] = timestamp
            # Convert timestamp to human readable format
            device_info["human_readable_time"] = datetime.fromtimestamp(
                int(str(timestamp)[:10])
            ).strftime("%c")

        # Tank level
        device_info["tank_level"] = last_reading.get("tank", 0)
        device_info["rounded_level"] = round(float(device_info["tank_level"]), 2)

        # Battery status
        if device_info["battery_warning"] and not device_info["battery_critical"]:
            device_info["battery_status"] = "Low"
            device_info["battery_message_key"] = "battery_low"
        elif device_info["battery_critical"]:
            device_info["battery_status"] = "Critical"
            device_info["battery_message_key"] = "battery_critical"
        else:
            device_info["battery_status"] = "Normal"
            device_info["battery_message_key"] = None

        # Generate status message
        device_info["status_message"] = (
            f"Last Read: {device_info['human_readable_time']} "
            f"Tank Level: {device_info['rounded_level']}% "
            f"Battery Status: {device_info['battery_status']}"
        )

        return device_info

    def create_message_dict(self, device_info):
        """Create a dictionary of notification messages"""
        if not device_info:
            return {}

        return {
            "status": device_info["status_message"],
            "battery_low": "Battery level is low",
            "battery_critical": (
                "Battery level is critical!\n"
                "Replace as soon as possible using Energizer L91 AA Lithium Batteries. "
                "See https://tankutility.com/batteries/ for details."
            ),
            "level_below_50": f"Tank level has dropped below 50%.\nCurrent reading: {device_info['rounded_level']}%",
            "level_below_40": f"Tank level has dropped below 40%.\nCurrent reading: {device_info['rounded_level']}%",
            "level_below_30": f"Tank level is low!\nCurrent reading: {device_info['rounded_level']}%",
        }

    def log_data(self, status_message):
        """Write status to log file in the original format"""
        now = datetime.now()
        cwd = os.getcwd()
        path_to_log = f"{cwd}/tank.log"

        try:
            if os.path.isfile(path_to_log):
                with open("tank.log", "a") as file:
                    file.write(f"\n{now} {status_message}")
            else:
                with open("tank.log", "w") as file:
                    file.write(f"\n{now} {status_message}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
            return False

    def send_notifications(self, device_info, message_dict):
        """Send notifications based on tank level and battery status"""
        if not device_info or not message_dict:
            return

        notifications_sent = []

        # Check tank level thresholds and send appropriate notifications
        tank_level = device_info["rounded_level"]
        for threshold, message_key in self.tank_level_thresholds.items():
            if tank_level <= threshold:
                self.logger.info(f"Tank level below {threshold}% - sending notification")
                message = pushover.push(message_dict[message_key])
                message.notification()
                notifications_sent.append(f"Tank level {threshold}%")
                break  # Only send the most severe notification

        # Check battery status and send notification if needed
        battery_message_key = device_info.get("battery_message_key")
        if battery_message_key and battery_message_key in message_dict:
            self.logger.info(f"Battery status {device_info['battery_status']} - sending notification")
            message = pushover.push(message_dict[battery_message_key])
            message.notification()
            notifications_sent.append(f"Battery {device_info['battery_status']}")

        return notifications_sent

    def run(self):
        """Main execution flow"""
        if not self.validate_environment():
            return False

        if not self.get_auth_token():
            return False

        if not self.get_devices():
            return False

        if not self.get_device_data():
            return False

        device_info = self.process_device_data()
        if not device_info:
            self.logger.error("Failed to process device data")
            return False

        # Log the current status
        self.logger.info(device_info["status_message"])

        # Write to log file in the original format
        self.log_data(device_info["status_message"])

        # Create message dictionary
        message_dict = self.create_message_dict(device_info)

        # Send notifications
        notifications = self.send_notifications(device_info, message_dict)
        if notifications:
            self.logger.info(f"Notifications sent: {', '.join(notifications)}")
        else:
            self.logger.info("No notifications needed to be sent")

        return True


if __name__ == "__main__":
    monitor = TankUtilityMonitor()
    success = monitor.run()
    sys.exit(0 if success else 1)