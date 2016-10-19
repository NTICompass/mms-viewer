"""
	MMS PDU Decoder
	By: Eric Siegel
	https://github.com/NTICompass/mms-viewer
"""
import struct, tempfile, shutil
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image # Pillow
from io import BytesIO

class MMSMessage:
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
		0x96: ("Subject", 'ascii'),
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

	# Needed for data decoding
	charsets = {
		0xEA: 'utf_8',
		0x83: 'ascii',
		0x84: 'iso8859_1',
		0x85: 'iso8859_2',
		0x86: 'iso8859_3',
		0x87: 'iso8859_4'
	}

	# Also needed for data decoding
	mime_types = {
		0x80: '*/*',
		0x81: 'text/*',
		0x82: 'text/html',
		0x83: 'text/plain',
		0x84: 'text/x-hdml',
		0x85: 'text/x-ttml',
		0x86: 'text/x-vCalendar',
		0x87: 'text/x-vCard',
		0x88: 'text/vnd.wap.wml',
		0x89: 'text/vnd.wap.wmlscript',
		0x8A: 'text/vnd.wap.wta-event',
		0x8B: 'multipart/*',
		0x8C: 'multipart/mixed',
		0x8D: 'multipart/form-data',
		0x8E: 'multipart/byterantes',
		0x8F: 'multipart/alternative',
		0x90: 'application/*',
		0x91: 'application/java-vm',
		0x92: 'application/x-www-form-urlencoded',
		0x93: 'application/x-hdmlc',
		0x94: 'application/vnd.wap.wmlc',
		0x95: 'application/vnd.wap.wmlscriptc',
		0x96: 'application/vnd.wap.wta-eventc',
		0x97: 'application/vnd.wap.uaprof',
		0x98: 'application/vnd.wap.wtls-ca-certificate',
		0x99: 'application/vnd.wap.wtls-user-certificate',
		0x9A: 'application/x-x509-ca-cert',
		0x9B: 'application/x-x509-user-cert',
		0x9C: 'image/*',
		0x9D: 'image/gif',
		0x9E: 'image/jpeg',
		0x9F: 'image/tiff',
		0xA0: 'image/png',
		0xA1: 'image/vnd.wap.wbmp',
		0xA2: 'application/vnd.wap.multipart.*',
		0xA3: 'application/vnd.wap.multipart.mixed',
		0xA4: 'application/vnd.wap.multipart.form-data',
		0xA5: 'application/vnd.wap.multipart.byteranges',
		0xA6: 'application/vnd.wap.multipart.alternative',
		0xA7: 'application/xml',
		0xA8: 'text/xml',
		0xA9: 'application/vnd.wap.wbxml',
		0xAA: 'application/x-x968-cross-cert',
		0xAB: 'application/x-x968-ca-cert',
		0xAC: 'application/x-x968-user-cert',
		0xAD: 'text/vnd.wap.si',
		0xAE: 'application/vnd.wap.sic',
		0xAF: 'text/vnd.wap.sl',
		0xB0: 'application/vnd.wap.slc',
		0xB1: 'text/vnd.wap.co',
		0xB2: 'application/vnd.wap.coc',
		0xB3: 'application/vnd.wap.multipart.related',
		0xB4: 'application/vnd.wap.sia',
		0xB5: 'text/vnd.wap.connectivity-xml',
		0xB6: 'application/vnd.wap.connectivity-wbxml',
		0xB7: 'application/pkcs7-mime',
		0xB8: 'application/vnd.wap.hashed-certificate',
		0xB9: 'application/vnd.wap.signed-certificate',
		0xBA: 'application/vnd.wap.cert-response',
		0xBB: 'application/xhtml+xml',
		0xBC: 'application/wml+xml',
		0xBD: 'text/css',
		0xBE: 'application/vnd.wap.mms-message',
		0xBF: 'application/vnd.wap.rollover-certificate',
		0xC0: 'application/vnd.wap.locc+wbxml',
		0xC1: 'application/vnd.wap.loc+xml',
		0xC2: 'application/vnd.syncml.dm+wbxml',
		0xC3: 'application/vnd.syncml.dm+xml',
		0xC4: 'application/vnd.syncml.notification',
		0xC5: 'application/vnd.wap.xhtml+xml',
		0xC6: 'application/vnd.wv.csp.cir',
		0xC7: 'application/vnd.oma.dd+xml',
		0xC8: 'application/vnd.oma.drm.message',
		0xC9: 'application/vnd.oma.drm.content',
		0xCA: 'application/vnd.oma.drm.rights+xml',
		0xCB: 'application/vnd.oma.drm.rights+wbxml'
	}

	def __init__(self, mms):
		self.data = mms

	def decode(self, use_pil=True):
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
			# 20-7F: Null-terminated string
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
				# Look up the MIME type in the table
				# This value may be a single byte
				byte_range = bytes([byte_range]) if type(byte_range) is int else byte_range
				if byte_range[0] in self.mime_types:
					value = self.mms_content_type = self.mime_types[byte_range[0]]

					# Read the type of the encapsulated data
					for content_header in byte_range[1:].rstrip(b'\x00').split(b'\x00'):
						# 0x89: Multipart Related Type
						if content_header.startswith(b'\x89'):
							# Save the encapsulated content-type separately
							self.content_type = content_header.lstrip(b'\x89').decode('utf_8')
						# 0x8A: Presentation Content ID
						elif content_header.startswith(b'\x8A'):
							# As well as this value, which I don't know how it's used
							self.content_id = content_header.lstrip(b'\x8A').decode('utf_8')
				else:
					value = ''
			elif method == 'from':
				# The "from" phone number
				# Phone numbers end in "/TYPE=PLMN", let's strip that off
				# The 1st byte is the "Address-present-token" (0x80)
				# The last byte is a null byte (trim that off)
				if byte_range.startswith(b'\x80'):
					value = byte_range.lstrip(b'\x80').rstrip(b'\x00').decode('utf_8').rstrip('/TYPE=PLMN')
				else:
					value = ''
			elif method == 'to':
				# This will be an array, just in case there are multiple values
				value = mms_headers[header] if header in mms_headers else []
				# Note: value is a *reference*, so we can just update and not set it
				value.append(byte_range.decode('utf_8').rstrip('/TYPE=PLMN'))
			elif method == 'ascii':
				# Convert the byte_range into an ASCII string
				value = byte_range.decode('utf_8')
			elif method == 'timestamp':
				# Decode the bytes into an timestamp
				# ie: convert b'\x57\xe2\xa2\x49' to 0x57e2a249 (1474470473)
				# With thanks to: http://codereview.stackexchange.com/a/142918/52
				# Note: Unpack always returns a tuple (even if it only contains one value)
				timestamp, = struct.unpack('>L', byte_range)
				value = datetime.fromtimestamp(timestamp)
			elif method == 'boolean':
				# A "boolean" is a yes/no value
				# 0x80 = yes and 0x81 = no
				value = byte_range == b'\x80'

			if header not in mms_headers:
				# If this is an array, then all we need is a reference to it
				# We can append to that and not need to set it back in the object
				mms_headers[header] = value

		# We've finished the headers, let's move onto the actual data
		# Continue reading bytes, except we now are filling in the data
		# The data is (probably) application/vnd.wap.multipart.related
		# It may not actually be.  In the case of an error, it's just text/plain
		if self.mms_content_type == 'text/plain':
			# This is just a txt file.
			# Just read the rest of the bytes and decode
			the_data = content_type_length = self.data[curr_index:].decode('utf_8')

			# Append the data to the array of parts
			mms_data.append({
				'fileName': None,
				'contentType': self.mms_content_type,
				'contentLength': len(the_data),
				'data': the_data
			})
		elif self.mms_content_type.startswith('application/vnd.wap.multipart'):
			# How many "parts" are in this "multipart" data?
			parts = self.data[curr_index]
			curr_index += 1

			# Loop over each part and get its data
			for x in range(0, parts):
				# The next byte tells us the length of the content type header
				data_header_length = self.data[curr_index]
				curr_index += 1
				data_header_index = 0

				# The next X bytes are the content length
				# We need to read bytes and convert them into octets until
				# the "continue bit" is 0.
				# The format is described in WAP-230 Section 8.1.2
				# "Variable Length Unsigned Ints"
				# Basically, you encode each hexit as binary,
				# break then into 7-bit chunks (the 1st bit is the "continue bit")
				# Then you glue them back together
				# Ex: 82 3F => 1000 0010 0011 1111
				# 1|0000010 0|0111111 => 00 0001 0011 1111 => 0x013F => 319
				# With help from: http://codereview.stackexchange.com/a/142939/52
				content_length = 0
				while True:
					byte = self.data[curr_index]
					curr_index += 1
					content_length = (content_length << 7) | (byte & 127)
					if byte >> 7 == 0:
						break

				# Get the full "data header", which contains the
				# Content-Type and Content-ID
				data_header = self.data[curr_index:curr_index+data_header_length]
				curr_index += data_header_length

				# Now, we get the content-type.
				# Read the next byte...
				# 00-1E: Read that many bytes
				# 1F: Next byte is length
				# 80-FF: This byte is the data
				# This range contains the content-type and its charset
				if 0x00 <= data_header[data_header_index] <= 0x1E:
					content_type_length = data_header[data_header_index]
					data_header_index += 1
				elif data_header[data_header_index] == 0x1F:
					content_type_length = data_header[data_header_index+1]
					data_header_index += 2
				elif 0x80 <= data_header[data_header_index] <= 0xFF:
					# This byte *is* the data
					# Don't shift data_header_index, just re-read this byte
					content_type_length = 1

				content_type_range = data_header[data_header_index:data_header_index+content_type_length]
				data_header_index += content_type_length

				# A single byte will be read as an int, convert it back to a bytes object
				content_type_range = bytes([content_type_range]) if type(content_type_range) is int else content_type_range

				# Get the content type, charset and file name
				# This may not always be set for all parts
				file_name = ''

				# How should we intrepret the content type?
				# Check the 1st byte:
				# 20-7F: Null-terminated string
				# 80-FF: This byte is the data
				if 0x20 <= content_type_range[0] <= 0x7F:
					# Read until we hit a null byte (0x00)
					data_content_type_length = content_type_range.index(0x00)

					# self.content_type should be application/smil
					# The 1st part will be this, but the 2nd can be anything
					data_content_type = content_type_range[0:data_content_type_length].decode('utf_8')

					# What charset is being used?  That's the next byte
					data_charset = self.charsets[content_type_range[data_content_type_length+1]]

					# The rest is the file name, followed by a null byte
					file_name = content_type_range[data_content_type_length+2:].rstrip(b'\x00').decode('utf_8')
				elif 0x80 <= content_type_range[0] <= 0xFF:
					# Look it up in the MIME type table
					data_content_type = self.mime_types[content_type_range[0]]

					# Is there any more data here?  A charset and (maybe) a file name.
					if len(content_type_range) > 1:
						# We may need to get more info out of this range, let's add a counter
						data_content_type_index = 1

						# What charset is being used, if any?
						# If there's an 0x85, this may mean "start of file name", and may not be the charset
						# There may sometimes be an 0x81 byte, which means the *next* byte is the charset
						if content_type_range[data_content_type_index] == 0x81:
							data_charset = self.charsets[content_type_range[data_content_type_index+1]]
							data_content_type_index += 2
						else:
							data_charset = self.charsets[content_type_range[data_content_type_index]]
							data_content_type_index += 1

						# Is there anything, like a file name, left?
						if len(content_type_range) > data_content_type_index:
							# The rest is the file name, followed by a null byte
							# Sometimes there's an 0x85 here.  Not sure why.
							# Pretty sure we already read the charset, and no longer need it.
							# Just strip it off, I guess.
							file_name = content_type_range[data_content_type_index:].lstrip(b'\x85').rstrip(b'\x00').decode('utf_8')

				# Followed by the "Content-ID" (this may not match the one from earlier)
				# This is just the rest of the remaining bytes before the data
				# I don't actually know what it is or how to decode it
				# It seems to contain the "file name", except multiple times for some reason
				# We've read the "content-type length" (1 byte) and the "content-type"
				# and the "file name", this is what's left in the data header
				data_content_id = data_header[data_header_index:]

				# The content type may not actually have the file name in it.
				# In this case, it's in the content id.
				# Let's attempt to extract it.
				if file_name == '' and data_content_id.startswith(b'\xAE\x0F\x81\x86'):
					# I don't know what these bytes mean, but the file name is after:
					# 0xAE 0x0F 0x81 0x86
					# and just read to NULL
					file_name = data_content_id[4:].rstrip(b'\x00').decode('utf_8')

				# Ok, we're done with the content headers.
				# We know the length of the data, let's read that many bytes!
				the_data = self.data[curr_index:curr_index+content_length]
				curr_index += content_length

				# "Decode" the data, or wrap it in an object
				if data_content_type.startswith('image/'):
					# Should we process the image with PIL or not?
					if use_pil:
						the_data = Image.open(BytesIO(the_data))
					else:
						# 5M of RAM before using a temp file on disk
						tmpFile = tempfile.SpooledTemporaryFile(5242880)
						tmpFile.write(the_data)
						tmpFile.seek(0)

						# Store the "file" object in as the data
						the_data = tmpFile
				elif data_content_type == 'application/smil':
					the_data = BeautifulSoup(the_data.decode(data_charset), 'xml')
				else:
					the_data = the_data.decode(data_charset)

				# Append the data to the array of parts
				mms_data.append({
					'fileName': file_name,
					'contentType': data_content_type,
					'contentLength': content_length,
					'data': the_data
				})

		return mms_headers, mms_data
