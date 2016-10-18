"""
	Virgin Mobile MMS Downloader
	By: Eric Siegel
	https://github.com/NTICompass/mms-viewer
"""
import urllib.request

class VirginMobile:
	"""
	Virgin Mobile uses multiple endpoints for different MMS messages.

	mmsc.vmobl.com:8088/mms/?XXX *should* work, but usually 404's
	rstnmmsc.vmobl.com seems to be used when the ID is 17 characters
	sobmmsc.vmobl.com seems to be used when it's 9 characters

	This is an object of tuples.  1st is the server, 2nd is the query parameter
	The key is the string length of the ID
	"""
	mms_servers = {
		17: ('rstnmmsc.vmobl.com', 'ammsc'),
		9: ('sobmmsc.vmobl.com', 'ammsc')
	}
	mms_port = '8088' # This is the default port for all servers

	"""
	If needed, we can send our request through a proxy

	For some reason, these seem to timeout when used
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

		# Which server do we use?  It seems to be based off of the length of the ID
		server, query = self.mms_servers[len(mms_id)]
		try:
			mms_download = urllib.request.urlopen("http://{0}:{1}/{2}?{3}".format(server, self.mms_port, query, mms_id), timeout=10)
		except urllib.error.URLError as error:
			print('MMS Download ({0}) Failed: {1} {2}'.format(server, error.code, error.reason))
			mms_data_stream = None
		else:
			print('MMS Downloaded {0} bytes from {1}'.format(mms_download.getheader('Content-Length'), server))
			mms_data_stream = mms_download

		return mms_data_stream
