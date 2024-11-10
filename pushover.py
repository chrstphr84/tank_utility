#!/python
'''
Description:
    Send push notification to phone using Pushover
Use:
    import pushover
    message = pushover.push('some message')
    message.notification()
'''
import http.client, urllib
import constants

class push:
    def __init__(self, message):
        self.message = message

    def notification(self):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": str(constants.pushOverToken),
            "user": str(constants.pushOverUser),
            "message": str(self.message),
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()
