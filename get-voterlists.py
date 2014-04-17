#!/usr/bin/python
"""
Retrieves voter lists from ceokarnataka.kar.nic.in . Depends on hardcoded paths.

Tested to get voter lists for Rajarajeshwari Nagar area, which in turn comes under Bangalore Rural.

Tested as :
./get_voterlists.py 154 338 338
"""
import sys
import os
import os.path
import subprocess

areaCode = int(sys.argv[1])
minIdx = int(sys.argv[2])
maxIdx = int(sys.argv[3])

# ceokarnataka.kar.nic.in has voter lists inside a specific directory.
# we can get voter lists with a simple get on the URL
# e.g. http://ceokarnataka.kar.nic.in/ElectionFinalroll2014/PCROLL_2014/English/WOIMG/AC154/AC1540347.pdf
# here : AC154 -> this is the number for your area
# 
urlFmt = 'http://ceokarnataka.kar.nic.in/ElectionFinalroll2014/PCROLL_2014/English/WOIMG/AC%d/AC%d%04d.pdf'

def getUrl(url, retries=10):
	# Retry to get URL. CEO karnataka website may not accept connections, especially on election day!
	fname = url.split('/')[-1]
	if os.path.isfile(fname):
		print 'File %s exists. Not getting from web'%(url)
		return
	print 'Retrieving URL %s... '%(url)
	for retry in range(retries):
		ret = subprocess.call(['wget', url])
		if ret == 0:
			return
		print '  Try %d(of %d)'%(retry+2, retries)
	print >> sys.stderr, "Failed to get file. Exiting..."
	sys.exit(1)

# Get all the files in a loop
for boothNo in range(minIdx, maxIdx+1):
	print 'Retrieving voter list for booth %d'%(boothNo)
	url = urlFmt%(areaCode, areaCode, boothNo)
	getUrl(url)
