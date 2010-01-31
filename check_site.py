URL = 'http://example.com'
REQUEST_TIMEOUT = 5 # Request timeout in seconds
USER_AGENT = 'checksitepy/0.1 (+http://github.com/donnex/checksitepy)'
OFFLINE_INTERVAL = 300 # 300 sec (5 min) for site to be considered offline
INTERVAL = 600 # Check every 600 sec (10 min) (only non-cron)

import sys
import urllib2
from time import time
from datetime import datetime, timedelta
try:
    import json
except ImportError:
    import simplejson as json

class CheckSite(object):
    def __init__(self, cron):
        self.url = URL
        self.request_timeout = REQUEST_TIMEOUT
        self.user_agent = USER_AGENT
        self.interval = INTERVAL
        self.status_file = '.checksite.status'

        if cron:
            self.check_site()
        else:
            from time import sleep
            while True:
                self.check_site()
                sleep(self.interval)

    def check_site(self):
        self.headers = {}
        if self.user_agent:
            self.headers['User-Agent'] = self.user_agent

        request = urllib2.Request(self.url, headers=self.headers)

        try:
            # Support Python 2.5 timeout
            try:
                self.content = urllib2.urlopen(request, timeout=self.request_timeout).read()
            except TypeError:
                import socket
                socket.setdefaulttimeout(self.request_timeout)
                self.content = urllib2.urlopen(request).read()
        except Exception:
            # import traceback
            # raise Exception('Generic exception: ' + traceback.format_exc())

            # Site is not reachable
            self.content = None
            self.site_status(online=False)

        # Site was reachable and we got content back
        if self.content:
            self.site_status(online=True)

    def site_status(self, online):
        self.last_status = self.get_last_status()
        # Site is online and last status was offline
        if online and self.last_status['online'] == False:
            offline_notification_sent = self.last_status.get('offline_notification_sent')
            if offline_notification_sent:
                self.send_status_change(u'%s is now back online.' % self.url)
            self.write_status(online=online)
        # Site is offline
        elif not online:
            offline_time_timestamp = self.last_status.get('offline_time')
            # Site has been offline in a previous check
            if offline_time_timestamp:
                offline_time = datetime.fromtimestamp(offline_time_timestamp)
                # Site has been offline longer than offline interval
                if datetime.now() - offline_time > timedelta(seconds=OFFLINE_INTERVAL):
                    offline_notification_sent = self.last_status.get('offline_notification_sent')
                    if not offline_notification_sent:
                        self.send_status_change(u'%s is now offline.' % self.url)
                        self.write_status(online=online, offline_time=offline_time_timestamp, offline_notification_sent=True)
            # First time site is offline
            else:
                self.write_status(online=online, offline_time=time())

    def get_last_status(self):
        try:
            f = open(self.status_file, 'r')
            s = f.read()
            f.close()
            status = json.loads(s)
            return status
        except IOError:
            status = {'online': False}
            return status

    def write_status(self, online, offline_time=None, offline_notification_sent=False):
        status = {
            'online': online,
            'offline_time': offline_time,
            'offline_notification_sent': offline_notification_sent
        }
        f = open(self.status_file, 'w')
        f.write(json.dumps(status))
        f.close()

    def send_status_change(self, message):
        print message


if __name__ == '__main__':
    # Run once (cron) or continue in loop
    if len(sys.argv) == 2 and sys.argv[1] == 'cron':
        cron = True
    else:
        cron = False

    try:
        CheckSite(cron)
    except KeyboardInterrupt:
        print 'Exiting..'