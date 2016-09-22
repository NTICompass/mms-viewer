"""
	Virgin Mobile MMS Downloader
	By: Eric Siegel
	https://github.com/NTICompass/mms-viewer
"""
import sys, urllib.request

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

# Parse the MMS PDU into an object
# Some info at http://support.nowsms.com/discus/messages/485/13726.html
# TODO: Totally don't steal code from http://python-mms.sourceforge.net/api/mms.mms_pdu-pysrc.html
class MMSMessage:
	# From: https://en.wikipedia.org/wiki/Cellular_data_communication_protocol#MMS.5Bjargon.5D
	# Each header value has its own unique way of being decoded
	# tuple: (name, length, method)
	#	length is:
	#		x: number of bytes
	#		0: Read until 0x00
	#		-1: Next byte is length
	mms_headers = {
		0x81: ("Bcc"),
		0x82: ("Cc"),
		0x83: ("X-Mms-Content-Location"),
		0x84: ("Content-Type"),
		0x85: ("Date"),
		0x86: ("X-Mms-Delivery-Report"),
		0x87: ("X-Mms-Delivery-Time"),
		0x88: ("X-Mms-Expiry"),
		0x89: ("From"),
		0x8A: ("X-mms-Message-Class"),
		0x8B: ("Message-ID"),
		0x8C: ("X-Mms-Message-Type", 1, 'messageType'),
		0x8D: ("X-Mms-MMS-Version"),
		0x8E: ("X-Mms-Message-Size"),
		0x8F: ("X-Mms-Priority"),
		0x90: ("X-Mms-Read-Report"),
		0x91: ("X-Mms-Report-Allowed"),
		0x92: ("X-Mms-Response-Status"),
		0x93: ("X-Mms-Response-Text"),
		0x94: ("X-Mms-Sender-Visibility"),
		0x95: ("X-Mms-Status"),
		0x96: ("Subject"),
		0x97: ("To"),
		0x98: ("X-Mms-Transaction-Id", 00, 'ascii'),
		0x99: ("X-Mms-Retrieve-Status"),
		0x9A: ("X-Mms-Retrieve-Text"),
		0x9B: ("X-Mms-Read-Status"),
		0x9C: ("X-Mms-Reply-Charging"),
		0x9D: ("X-Mms-Reply-Charging-Deadline"),
		0x9E: ("X-Mms-Reply-Charging-ID"),
		0x9F: ("X-Mms-Reply-Charging-Size"),
		0xA0: ("X-Mms-Previously-Sent-By"),
		0xA1: ("X-Mms-Previously-Sent-Date")
	}
	# Values for header 0x8C
	mms_message_type = {
		0x80: "m-send-req",
		0x81: "m-send-conf",
		0x82: "m-notification-ind",
		0x83: "m-notifyresp-ind",
		0x84: "m-retrieve-conf",
		0x85: "m-acknowledge-ind",
		0x86: "m-delivery-ind",
		0x87: "m-read-rec-ind",
		0x88: "m-read-orig-ind",
		0x89: "m-forward-req",
		0x8A: "m-forward-conf"
	}

	def __init__(self, mms):
		self.data = mms

	def decode(self):
		# Start looping over each byte in the data.
		# Assume the 1st byte is a header code and then start decoding.
		mms_result = {}

		curr_index = 0
		while curr_index < len(self.data):
			# Get the header
			curr_byte = self.data[curr_index]
			# and its parsing info
			header, length, method = self.mms_headers[curr_byte]

			# Decode the value...
			value = None
			# First read the length of bytes we need
			if length > 0:
				# Set number of bytes
				curr_index += 1
				byte_range = self.data[curr_index:curr_index+length]

				curr_index += length
			elif length == -1:
				# Next type is the length
				curr_index += 1
				byte_count = self.data[curr_index]

				curr_index += 1
				byte_range = self.data[curr_index:byte_count]

				curr_index += byte_count
			elif length == 0:
				# Read until we hit a 0x00
				byte_range = bytearray()

				curr_index += 1
				while self.data[curr_index] != 0x00:
					byte_range.append(self.data[curr_index])
					curr_index += 1

			# Then decide what to do with those bytes
			if method == 'messageType':
				# Get the message type
				value = self.mms_message_type[byte_range]
			elif method == 'ascii':
				# Convert the byte_range into an ASCII string
				value = byte_range
				print(value)
				sys.exit(0)

			mms_result[header] = value

if __name__ == '__main__':
	phone = VirginMobile('15555555555')
	try:
		#message = phone.download('mms-id', proxy=False)
		message = open('mms_response.bin', 'rb')
	except urllib.error.URLError as error:
		print(error.reason)
	else:
		# The data has a Content-Type of application/vnd.wap.mms-message
		mms_data = message.read()

		# Decode the message
		decoder = MMSMessage(mms_data)
		mms_result = decoder.decode()
