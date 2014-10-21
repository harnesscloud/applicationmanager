#!/usr/bin/env python
from StringIO import StringIO

from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from twisted.web.client import FileBodyProducer
import sys

if len(sys.argv) < 2:
	print "Specify the slo file as parameter."
	sys.exit(0)
agent = Agent(reactor)

body = FileBodyProducer(open(sys.argv[1], "r"))
d = agent.request(
    'POST',
    'http://localhost:5556/ExecuteApplication',
    Headers({'User-Agent': ['Twisted Web Client Example'],
             'Content-Type': ['text/x-greeting']}),
    body)

def cbResponse(ignored):
    print 'Response received'
d.addCallback(cbResponse)

def cbShutdown(ignored):
    reactor.stop()
d.addBoth(cbShutdown)

reactor.run()



























import httplib, mimetypes

def post_multipart(host, uri, fields, files):
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTPConnection(host)
    headers = {
        'User-Agent': 'INSERT USERAGENTNAME',
        'Content-Type': content_type
        }
    h.request('POST', uri, body, headers)
    res = h.getresponse()
    return res.status, res.reason, res.read() 

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------bound@ry_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

