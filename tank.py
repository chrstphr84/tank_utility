#!/env/python3
#
# This script pulls data from Tank Utility's API.
import json
import os
from datetime import datetime

import constants
import pushover
import requests

try:
    response = requests.get(
        "https://data.tankutility.com/api/getToken",  # This is NOT a secure call.
        auth=(f"{str(constants.tankUtilityUser)}", f"{str(constants.tankUtilityPw)}"),
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("token")

except requests.exceptions.HTTPError as err:
    dataErr = json.loads(err.response.text)
    print(
        "HTTP ERROR: "
        + str(dataErr["statusCode"])
        + " "
        + str(err.response.status_code)
    )
    print("DETAIL: " + str(dataErr["error"]))
    raise SystemExit()

except requests.exceptions.ConnectionError as connErr:
    print("NETWORK CONNECTION ERROR:: " + str(connErr))
    raise SystemExit()


# Get a list of devices
devices = requests.get(f"https://data.tankutility.com/api/devices?token={token}")
device_data = devices.json()
device_id = device_data.get("devices")
response = requests.get(
    f"https://data.tankutility.com/api/devices/{device_id[0]}?token={token}"
)
response_data = response.json()

# Device information
device_name = response_data["device"]["name"]
battery_critical = response_data["device"]["battery_crit"]
battery_warning = response_data["device"]["battery_warn"]
average_consumption = response_data["device"]["average_consumption"]
temperature = response_data["device"]["lastReading"]["temperature"]

# Time
time = response_data["device"]["lastReading"]["time"]
human_readable_time = datetime.fromtimestamp(int(str(time)[:10])).strftime("%c")

# Levels
lastReading = response_data["device"]["lastReading"]["tank"]
rounded_reading = round(float(lastReading), 2)  # round to nearest hundredth


if battery_warning and not battery_critical:
    battery_status = "Low"
    message_key = "battery_low"

elif battery_critical:
    battery_status = "Critical"
    message_key = "battery_critical"

else:
    battery_status = "Normal"


current_status = f"Last Read: {human_readable_time} Tank Level: {rounded_reading}% Battery Status: {battery_status} "

print(current_status)

message_dict = {
    "status": current_status,
    "battery_low": "Battery level is low",
    "battery_critical": "Battery level is critical!\nReplace as soon as possible using Energizer L91 AA Lithium Batteries. See https://tankutility.com/batteries/ for details.",
    "level_below_50": f"Tank level has dropped below 50%.\nCurrent reading: {rounded_reading}%",
    "level_below_40": f"Tank level has dropped below 40%.\nCurrent reading: {rounded_reading}%",
    "level_below_30": f"Tank level is low!\nCurrent reading: {rounded_reading}%",
}


def push_tank_level():
    if lastReading <= 30.00:
        message = pushover.push(message_dict["level_below_30"])
        message.notification()

    else:
        # readingMessage = ""
        pass


def push_battery_status():
    if battery_critical:
        message = pushover.push(message_dict["battery_critical"])
        message.notification()

    else:
        battery_message = ""


def log_data():
    now = datetime.now()
    cwd = os.getcwd()
    path_to_log = f"{cwd}/tank.log"
    if os.path.isfile(path_to_log):
        with open("tank.log", "a") as file:
            file.write(f"\n{now} {current_status}")
    else:
        with open("tank.log", "w") as file:
            file.write(f"\n{now} {current_status}")


push_tank_level()
push_battery_status()
log_data()


# TODO Clean up code
