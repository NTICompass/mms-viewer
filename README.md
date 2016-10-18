# mms-viewer
A crappy python script to download/parse MMS messages.

I used a lot of references to create the MMS decoder.
Such as the MMS spec:
- v1.3: http://technical.openmobilealliance.org/Technical/release_program/docs/MMS/V1_3-20080128-C/OMA-TS-MMS-ENC-V1_3-20080128-C.pdf

- v1.2: http://technical.openmobilealliance.org/Technical/release_program/docs/MMS/V1_2-20050429-A/OMA-MMS-ENC-V1_2-20050301-A.pdf

And WAP-230: http://www.wapforum.org/tech/documents/WAP-230-WSP-20010705-a.pdf

Other references:
- http://support.nowsms.com/discus/messages/485/13726.html
- http://support.nowsms.com/discus/messages/485/6597538470-D8751867A0B-13774.txt
- http://www.nowsms.com/send-an-mms-to-a-java-appmidlet
- http://python-mms.sourceforge.net/api/mms.mms_pdu-pysrc.html
- https://github.com/heyman/mms-decoder/blob/master/mmsdecoder.php
- https://en.wikipedia.org/wiki/Cellular_data_communication_protocol#MMS.5Bjargon.5D
- https://www.wireshark.org/docs/dfref/m/mmse.html

Note to self: JPEG "hex signature" is: FF D8 FF E1
PNG is: 89 50 4E 47 0D 0A 1A 0A
https://en.wikipedia.org/wiki/List_of_file_signatures
