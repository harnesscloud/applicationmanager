#!/usr/bin/env python
import urllib

class Converter:
	@staticmethod
	def get_size(path):
		meta = urllib.urlopen(path)
		val = meta.info()['Content-Length']/1024. / 1024.
		#it is in bytes, convert to GB
		return val
