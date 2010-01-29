URL = 'http://example.com'
REQUEST_TIMEOUT = 5
USER_AGENT = None
INTERVAL = 600 # 10 min

import sys
import urllib2
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

        request = urllib2.Request(self.url, self.headers)

        try:
            self.content = urllib2.urlopen(request, timeout=self.request_timeout).read()
        except Exception:
            # import traceback
            # raise Exception('Generic exception: ' + traceback.format_exc())

            # Site is not reachable log time as failure
            self.site_status(online=False)

        # Site was reachable and we got content back
        if self.content:
            self.site_status(online=True)

    def site_status(self, online):
        self.last_status = self.get_last_status()
        # Site is online and last status was offline
        if online and self.last_status['online'] == False:
            self.send_status_change(u'%s is now back online.' % self.url)
        # Site is offline and last status was online
        elif not online and self.last_status['online'] == True:
            self.send_status_change(u'%s is now offline.' % self.url)

        self.write_status(online=online)

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
            
    def write_status(self, online):
        status = {'online': online}
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