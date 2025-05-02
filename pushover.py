#!/usr/bin/env python3
'''
Description:
    Send push notification to phone using Pushover
Use:
    import pushover
    message = pushover.push('some message')
    message.notification()
'''
import http.client
import urllib
import logging
import constants


class push:
    def __init__(self, message, title=None, priority=0):
        self.message = message
        self.title = title
        self.priority = priority
        self.logger = logging.getLogger("tank_utility.pushover")

    def notification(self):
        """Send a notification via Pushover API"""
        if not constants.pushOverUser or not constants.pushOverToken:
            self.logger.error("Pushover credentials missing")
            return False

        try:
            conn = http.client.HTTPSConnection("api.pushover.net:443", timeout=10)

            # Build the request data
            post_data = {
                "token": str(constants.pushOverToken),
                "user": str(constants.pushOverUser),
                "message": str(self.message),
            }

            # Add optional parameters if provided
            if self.title:
                post_data["title"] = str(self.title)

            if self.priority:
                post_data["priority"] = self.priority

            # Send the request
            conn.request(
                "POST",
                "/1/messages.json",
                urllib.parse.urlencode(post_data),
                {"Content-type": "application/x-www-form-urlencoded"}
            )

            # Get and process the response
            response = conn.getresponse()
            response_data = response.read().decode("utf-8")

            if response.status != 200:
                self.logger.error(f"Pushover API error: {response.status} {response_data}")
                return False

            self.logger.debug(f"Pushover notification sent successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send Pushover notification: {e}")
            return False