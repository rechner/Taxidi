"""Sends an alert to a remote OpenLP instance over JSON."""

__all__ = ['OpenLP']

import json
import urllib, urllib2
import logging

class OpenLP:
    def __init__(self, server, port, url="http://{server}:{port}/api/alert?"):
        """
        Class for sending alerts to a remote OpenLP instance.
        Accepts server, port, and an optional custom url.
        ( Default: http://{server}:{port}/api/alert? )
        """
        self.log = logging.getLogger(__name__)
        self.url = url.format(server=server, port=port)

    def send(self, alert):
        """Sends a notification."""
        jdata = json.dumps({"request": {"text": alert}})

        try:
            response = urllib2.urlopen(self.url
                + urllib.urlencode({'data' : jdata}))
        except urllib2.URLError as e:
            self.log.error('Error while sending request for {0}'.format(self.url))
            self.log.error('Server returned: {0}'.format(e))
            raise NotificationError('{0}'.format(e), code=e.code)

        json_data = json.loads(response.read())
        if json_data['results']['success']:
            return 0 #all good :3
        else:
            raise NotificationError('Notification sending failed: {0}'.format(e))

class NotificationError(Exception):
        def __init__(self, value='', json_data='', code=''):
            self.code = code
            self.json = json_data
            if value == '':
                self.error = 'Generic OpenLP error response: {0}'.format(json_data)
            else:
                self.error = value + json_data
        def __str__(self):
            return repr(self.error)

if __name__ == '__main__':
    alert = "Parents: watch for your child's number - E-9999"
    server = '192.168.2.103'
    port = 4316
    notify = OpenLP(server, port)
    notify.send(alert)
