#!/usr/bin/env python3
import argparse
from VirginMobile import VirginMobile
from MMSMessage import MMSMessage
from PhoneBook import PhoneBook

version = "0.4 alpha"

parser = argparse.ArgumentParser(
	description="MMS Viewer v{0}: An MMS Downloader and Decoder".format(version),
	epilog="https://github.com/NTICompass/mms-viewer"
)

parser.add_argument('-V', '--version', action='version', version=version)

parser.add_argument("file_or_phone", help="MMS File or phone number")
parser.add_argument("mmsid", nargs="?", help="MMS-Transaction-ID")
parser.add_argument('-p', '--phonebook', help="Use phonebook.db", action="store_true")

parser.add_argument('--debug', help="Print debugging info", action="store_true")

group = parser.add_mutually_exclusive_group()
group.add_argument('-x', '--extract', help="Extract image file(s)", action="store_true")
group.add_argument('-X', '--extract-original', help="Extract original image file(s) without using PIL", action="store_true")

args = parser.parse_args()

if args.mmsid is not None:
	phone = VirginMobile(args.file_or_phone)
	message = phone.download(args.mmsid, proxy=False)
else:
	message = open(args.file_or_phone, 'rb')

# Check if the file was downloaded successfully
if message is not None:
	# Get the data from the resource
	mms_data = message.read()

	# Decode the message
	decoder = MMSMessage(mms_data)
	mms_headers, mms_data = decoder.decode(use_pil=not args.extract_original)

	# Close the file/urllib.request object
	message.close()

	if args.debug:
		print(mms_headers)
		print(mms_data)

	# Did we get a successful message or an error?
	if mms_headers['Content-Type'] == 'text/plain':
		# MMS message contains an error message
		print('MMS Error:', mms_data[0]['data'])
	elif mms_headers['Content-Type'].startswith('application/vnd.wap.multipart'):
		# Print out some of the more important headers

		# Look up names in our phonebook
		if(args.phonebook):
			phonebook = PhoneBook()

			from_name = phonebook.get_name(mms_headers['From'])
			print("From:\n\t", ' '.join(from_name) if from_name is not None else mms_headers['From'])

			to_names = phonebook.get_names(mms_headers['To'])
			to_names = [' '.join(to_names[to]).rstrip(' ') if to in to_names else to for to in mms_headers['To']]
			print("To:\n\t", to_names)
		else:
			print("From:\n\t", mms_headers['From'])
			print("To:\n\t", mms_headers['To'])

		print("Date:\n\t", mms_headers['Date'].strftime('%A, %B %-d, %Y, %-I:%M %p'))
		if 'Subject' in mms_headers:
			print("Subject:\n\t", mms_headers['Subject'])
		print("Message:\n\t", [(file_data['contentType'], file_data['contentLength']) for file_data in mms_data])

		# Loop over the data and decide what to do with it
		for file_data in mms_data:
			# We have an image.  Should we extract it?
			if file_data['contentType'].startswith('image/'):
				# The file could be stored as either a PIL object or a temp file
				if args.extract:
					# Only JPEGs can have EXIFs (most cell phones will add this when texting an image)
					if file_data['contentType'] == ' image/jpeg':
						file_data['data'].save(file_data['fileName'], 'jpeg', exif=file_data['data'].info["exif"])
					else:
						file_data['data'].save(file_data['fileName'])
				elif args.extract_original:
					real_file = open(file_data['fileName'], 'wb')
					shutil.copyfileobj(file_data['data'], real_file)
					real_file.close()

				file_data['data'].close()
				print("Image Saved As:\n\t", file_data['fileName'])
			# This is just a text, display it
			elif file_data['contentType'] == 'text/plain':
				print("Text:\n\t", file_data['data'])
