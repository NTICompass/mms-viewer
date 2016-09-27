"""
	Virgin Mobile MMS Downloader
	By: Eric Siegel
	https://github.com/NTICompass/mms-viewer
"""
import sys, urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

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
# More into at http://technical.openmobilealliance.org/Technical/release_program/docs/MMS/V1_2-20050429-A/OMA-MMS-ENC-V1_2-20050301-A.pdf
# Or at: http://technical.openmobilealliance.org/Technical/release_program/docs/MMS/V1_3-20080128-C/OMA-TS-MMS-ENC-V1_3-20080128-C.pdf
# TODO: Totally don't steal code from http://python-mms.sourceforge.net/api/mms.mms_pdu-pysrc.html
# TODO: More code I shouldn't steal from: https://github.com/heyman/mms-decoder/blob/master/mmsdecoder.php
class MMSMessage:
	# From: https://en.wikipedia.org/wiki/Cellular_data_communication_protocol#MMS.5Bjargon.5D
	# See also: https://www.wireshark.org/docs/dfref/m/mmse.html
	# Decoding example: http://support.nowsms.com/discus/messages/485/6597538470-D8751867A0B-13774.txt
	# MMS Content Type info: http://www.nowsms.com/send-an-mms-to-a-java-appmidlet
	# Each header value has its own unique way of being decoded
	# tuple: (name, method)
	# See: http://www.wapforum.org/tech/documents/WAP-230-WSP-20010705-a.pdf (see section 8.4.1.2)
	# Turns out the 1st byte after the header (which may be *part* of the data), tells us how to interpret the length
	mms_headers = {
		0x81: ("Bcc"),
		0x82: ("Cc"),
		0x83: ("X-Mms-Content-Location"),
		# http://python-mms.sourceforge.net/api/mms.wsp_pdu.Decoder-class.html#decodeContentTypeValue
		0x84: ("Content-Type", "contentType"),
		0x85: ("Date", 'timestamp'),
		0x86: ("X-Mms-Delivery-Report", "boolean"),
		0x87: ("X-Mms-Delivery-Time"),
		0x88: ("X-Mms-Expiry"),
		0x89: ("From", 'from'),
		0x8A: ("X-mms-Message-Class", "messageClass"),
		0x8B: ("Message-ID", 'ascii'),
		0x8C: ("X-Mms-Message-Type", "messageType"),
		0x8D: ("X-Mms-MMS-Version", "version"),
		0x8E: ("X-Mms-Message-Size"),
		0x8F: ("X-Mms-Priority", "messagePriority"),
		0x90: ("X-Mms-Read-Report"),
		0x91: ("X-Mms-Report-Allowed"),
		0x92: ("X-Mms-Response-Status"),
		0x93: ("X-Mms-Response-Text"),
		0x94: ("X-Mms-Sender-Visibility"),
		0x95: ("X-Mms-Status"),
		0x96: ("Subject"),
		0x97: ("To", 'to'), # Note: There can be multiple "To" values
		0x98: ("X-Mms-Transaction-Id", "ascii"),
		0x99: ("X-Mms-Retrieve-Status", "boolean"),
		0x9A: ("X-Mms-Retrieve-Text", "ascii"),
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
	# Values for header 0x8D
	# From: https://godoc.org/github.com/ubuntu-phonedations/nuntium/mms
	mms_version = {
		0x90: '1.0',
		0x91: '1.1',
		0x92: '1.2',
		0x93: '1.3'
	}
	# Values for header 0x8A
	mms_message_class = {
		0x80: 'Personal',
		0x81: 'Advertisement',
		0x82: 'Informational',
		0x83: 'Auto'
	}
	# Values for header 0x8F
	mms_message_priority = {
		0x80: 'Low',
		0x81: 'Normal',
		0x82: 'High'
	}

	def __init__(self, mms):
		self.data = mms

	def decode(self):
		# Start looping over each byte in the data.
		# Assume the 1st byte is a header code and then start decoding.
		# Info on byte/bytearray: https://docs.python.org/3/library/stdtypes.html
		mms_headers = {}
		mms_data = []

		curr_index = 0
		# First get the headers from the data
		while curr_index < len(self.data):
			# Get the header...
			curr_byte = self.data[curr_index]
			# Once we hit a byte not in the header object, then we're done with the headers
			# Or we've just hit a header I haven't parsed yet
			if curr_byte not in self.mms_headers or len(self.mms_headers[curr_byte]) != 2:
				break
			# ...and its parsing info
			header, method = self.mms_headers[curr_byte]

			# Decode the value...
			value = None
			# Shift to the next byte
			curr_index += 1

			# Figure out the length of this header's value
			# Read the next byte...
			# 00-1E: Read that many bytes
			# 1F: Next byte is length
			# 20-7F: Null-terminated strng
			# 80-FF: This byte is the data
			header_length = self.data[curr_index]

			if 0 <= header_length <= 0x1E:
				# This byte is the length of the data
				# So read that many bytes ahead
				# After shifting to the start of the data
				curr_index +=1
				byte_range = self.data[curr_index:curr_index+header_length]
				# Shift over that many bytes
				curr_index += header_length
			elif header_length == 0x1F:
				# The next byte is the length
				curr_index += 1
				byte_count = self.data[curr_index]
				# Shift to the start of the data
				curr_index += 1

				# Read and shift the correct number of bytes
				byte_range = self.data[curr_index:curr_index+byte_count]
				curr_index += byte_count
			elif 0x20 <= header_length <= 0x7F:
				# Read until we hit a null byte (0x00)
				# The `header_length` byte is part of our data
				byte_range = bytearray()
				while self.data[curr_index] != 0x00:
					byte_range.append(self.data[curr_index])
					curr_index += 1

				# Shift off the null byte
				curr_index += 1
			elif 0x80 <= header_length <= 0xFF:
				# This byte is actually the value
				# So just return it and move on
				byte_range = self.data[curr_index]
				curr_index += 1

			# Then decide what to do with those byte(s)
			if method == 'messageType':
				# Get the message type
				value = self.mms_message_type[byte_range]
			elif method == 'version':
				# Get the mms version number
				value = self.mms_version[byte_range]
			elif method == 'messageClass':
				# Get the "message class"
				value = self.mms_message_class[byte_range]
			elif method == 'messagePriority':
				# Get the "message priority"
				value = self.mms_message_priority[byte_range]
			elif method == 'contentType':
				# The 1st byte tells us how to interpret the content type
				# Either "Content-general-form" or "Constrained-media"
				# The 2nd byte tells us whether the content type
				# is an ascii string, or a byte (to be looked up in a table)
				if byte_range.startswith(b'\xB3'): # application/vnd.wap.multipart.related
					for content_header in byte_range.lstrip(b'\xB3').rstrip(b'\x00').split(b'\x00'):
						# 0x89: Multipart Related Type
						if content_header.startswith(b'\x89'):
							# Save the content-type separately
							self.content_type = value = content_header.lstrip(b'\x89').decode('utf_8')
						# 0x8A: Presentation Content ID
						elif content_header.startswith(b'\x8A'):
							# As well as this value, which I don't know how it's used
							self.content_id = content_header.lstrip(b'\x8A').decode('utf_8')
				else:
					value = ''
			elif method == 'from':
				# The "from" phone number
				# The 1st byte is the "Address-present-token" (0x80)
				# The last byte is a null byte (trim that off)
				if byte_range.startswith(b'\x80'):
					value = byte_range.lstrip(b'\x80').rstrip(b'\x00').decode('utf_8')
				else:
					value = ''
			elif method == 'to':
				# This will be an array, just in case there are multiple values
				value = mms_headers[header] if header in mms_headers else []
				# Note: value is a *reference*, so we can just update and not set it
				value.append(byte_range.decode('utf_8'))
			elif method == 'ascii':
				# Convert the byte_range into an ASCII string
				value = byte_range.decode('utf_8')
			elif method == 'timestamp':
				# Decode the bytes into an timestamp
				# TODO: There's got to be a better way to convert a
				# bytearray/bytes object into an int
				# ie: convert b'\x57\xe2\xa2\x49' to 0x57e2a249 (1474470473)
				timestamp = int(''.join(map(hex, byte_range)).replace('0x', ''), 16)
				value = datetime.fromtimestamp(timestamp)
			elif method == 'boolean':
				# A "boolean" is a yes/no value
				# 0x80 = yes and 0x81 = no
				value = byte_range == b'\x80'

			if header not in mms_headers:
				# If this is an array, then all we need is a reference to it
				# We can append to that and not need to set it back in the object
				print('Decoded {0}'.format(header))
				mms_headers[header] = value

		# We've finished the headers, let's move onto the actual data
		print(mms_headers)
		# Continue reading bytes, except we now are filling in the data
		while curr_index < len(self.data):
			break

		return mms_headers, mms_data

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
		mms_headers, mms_data = decoder.decode()

		print(decoder.content_type, mms_data)
