"""
    Virgin Mobile MMS Downloader
    By: Eric Siegel
    https://github.com/NTICompass/mms-viewer
"""
import urllib.request

class VirginMobile:
    """
    Virgin Mobile normally uses mmsc as its endpoint,
    but sometimes it needs rstnmmsc or sobmmsc.

    This is an array of tuples.  1st is the server, 2nd is the query parameter
    """
    mms_servers = [
        ('mmsc.vmobl.com', 'mms'),
        ('rstnmmsc.vmobl.com', 'ammsc'),
        ('sobmmsc.vmobl.com', 'ammsc')
    ]
    mms_port = '8088' # This is the default port for all servers

    """
    If needed, we can send our request through a proxy
    """
    mms_proxy = [
        ('205.239.233.136', '81'),
        ('68.28.31.7', '80')
    ]
    mms_proxy_auth = ('Sprint', '*')

    # Create a new object with your phone number to download MMS messages
    def __init__(self, phone_num):
        self.phone_num = phone_num

    # Pass the MMS ID (I get it from Signal's logs) to download it from the server
    def download(self, mms_id, proxy=True):
        # Create the opener, it'll need to send the `X-MDN` header and may need to use a proxy
        if proxy:
            # TODO: Loop and try each proxy
            proxy_auth = ':'.join(self.mms_proxy_auth)
            proxy_server = ':'.join(self.mms_proxy[0])

            proxy = urllib.request.ProxyHandler({'http': "http://{0}@{1}".format(proxy_auth, proxy_server)})
            opener = urllib.request.build_opener(proxy)
        else:
            opener = urllib.request.build_opener()

        opener.addheaders = [('X-MDN', self.phone_num)]
        urllib.request.install_opener(opener)

        # TODO: Loop over servers until one works
        server, query = self.mms_servers[1]
        return urllib.request.urlopen("http://{0}:{1}/{2}?{3}".format(server, self.mms_port, query, mms_id), timeout=10)

if __name__ == '__main__':
    phone = VirginMobile('15555555555')
    try:
        message = phone.download('mms-id', proxy=False)
    except urllib.error.URLError as error:
        print(error.reason)
    else:
        # The data has a Content-Type of application/vnd.wap.mms-message
        mms_data = message.read()

        # TODO: Totally don't steal code from http://python-mms.sourceforge.net/api/mms.mms_pdu-pysrc.html
        # Info available at: https://en.wikipedia.org/wiki/Cellular_data_communication_protocol#MMS.5Bjargon.5D
