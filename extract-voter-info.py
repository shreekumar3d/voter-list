#!/usr/bin/python
"""
Extract voter list info from all PDF files in conv directory.

The only hardcoded thing in this file is the boothKey.

This spits out data in the following format:

booth number, sl no,  EPIC number, name.

If the sl no is in unicode, you'll see a "U 0" in its place. If the name is
in unicode, you'd see "(Unicode encoded)" there!
"""
import os
import re
from glob import glob
import sys
from pprint import pprint

# Manually generated from :
#  ceokarnataka.kar.nic.in/ElectionFinalroll2014/Part_List.aspx?ACNO=154
# Maps a booth number to an address
# Note : does NOT contain list for whole consituency, only a subset.
boothKey = {
310:'Rajarajeshwari Vidyasala, Room No-2, Kenchenahalli, Rajarajeshwarinagar Bangalore-98',
311:'Govt.Primary School, Room No-1, Mutturayanagar, Bangalore',
312:'Rajarajeshwari Vidyasala, Room No-3, Kenchenahalli, Rajarajeshwarinagar Bangalore-98',
313:'Rajarajeshwari Vidyasala, Room No-3, Kenchenahalli, Rajarajeshwarinagar Bangalore-98',
313:'Rajarajeshwari Vidyasala, Room No-04, Kenchenahalli, Rajarajeshwarinagar Bangalore-98',
314:'Mount Cormel English School, Room No-1, Halagevaderahalli, Rajarajeshwarinagar Bangalore-98',
315:'Mount Cormel English School, Room No-1, Halagevaderahalli, Rajarajeshwarinagar Bangalore-98',
315:'Mount Cormel English School, Room No-2, Halagevaderahalli, Rajarajeshwarinagar Bangalore-98',
316:'Mount Cormel English School, Room No-2, Halagevaderahalli, Rajarajeshwarinagar Bangalore-98',
317:'Mount Cormel English School, Room No-4, Halagevaderahalli, Rajarajeshwarinagar Bangalore-98',
318:'Mount Cormel English School, Room No-5, Halagevaderahalli, Rajarajeshwarinagar Bangalore-98',
319:'Govt. Higher Primary School, Room No-1, Bangarappanagar, hosakerehalli Bangalore',
320:'Govt. Higher Primary School, Room No-2, Bangarappanagar, hosakerehalli Bangalore',
321:'Govt. Higher Primary School, Room No-3, Bangarappanagar, Hosakerehalli Bangalore',
322:'Govt. Higher Primary School, Room No-4, Bangarappanagar, Hosakerehalli Bangalore',
323:'B.E.T. School, Room No-01, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
324:'B.E.T. School, Room No-02, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
325:'B.E.T. School, Room No-03, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
326:'B.E.T. School, Room No-04, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
327:'B.E.T. School, Room No-05, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
328:'B.E.T. School, Room No-05, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
329:'B.E.T. School, Room No-07, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
330:'B.E.T. School, Room No-07, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
331:'B.E.T. School, Room No-08, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
332:'B.E.T. School, Room No-08, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
333:'New Horizon Public School, Room No-01, BEML Layout 5th Stage, Rajarajeshwarinagar, Bangalore-98',
334:'New Horizon Public School, Room No-01, BEML Layout 5th Stage, Rajarajeshwarinagar, Bangalore-98',
335:'New Horizon Public School, Room No-01, BEML Layout 5th Stage, Rajarajeshwarinagar, Bangalore-98',
336:'New Horizon Public School, Room No-01, BEML Layout 5th Stage, Rajarajeshwarinagar, Bangalore-98',
337:'New Horizon Public School, Room No-01, BEML Layout 5th Stage, Rajarajeshwarinagar, Bangalore-98',
338:'New Horizon Public School, Room No-01, BEML Layout 5th Stage, Rajarajeshwarinagar, Bangalore-98',
339:'B.E.T. School, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
340:'B.E.T. School, 3rd Stage, BEML Layout, Rajarajeshwarinagar, Bangalore-98',
341:'Govt. Higher Primary School, Room No-1, Halagevaderahalli, Rajarajeshwarinagar, Bangalore-98',
342:'Govt. Higher Primary School, Room No-1, Halagevaderahalli, Rajarajeshwarinagar, Bangalore-98',
343:'Govt. Higher Primary School, Room No-1, Halagevaderahalli, Rajarajeshwarinagar, Bangalore-98',
344:'Govt. Higher Primary School, Room No-1, Halagevaderahalli, Rajarajeshwarinagar, Bangalore-98',
345:'Govt. Higher Primary School, Room No-1',
346:'Govt. Higher Primary School, Room No-2',
347:'Govt. Higher Primary School, Room No-3',
348:'Govt. Higer Primary School, Room No-4',
}

prefixList = []

def dumpVoterList(outfile, fname):
	"""
	Takes a voter list PDF file that has text in a non-encoded
	format (i.e. not using FlateDecoding). Use convert.sh to
	convert files downloaded from the ceokarnataka.kar.nic.in
	website.
	"""
	#f = open('conv/AC1540338.pdf', 'r')
	f = open(fname, 'r')
	boothNo = fname[-7:-4]
	slMatch = re.compile('^.*Td \(([R#]?\s*[0-9]+\s*)\).*$')
	rejMatch = re.compile('^.*Td \(([A-Z]{3}[0-9\s]+)\).*$')
	tdMatch = re.compile('^.*Td \((.*)\).*$')

	allLines = f.readlines()
	slNo = None
	prevTds = []
	tdSave = 7

	voterList = []
	for line in allLines:
		obj = tdMatch.match(line)
		if obj:
			newTd = obj.groups()[0]
			if len(prevTds)>tdSave:
				prevTds.pop(0)
			prevTds.append(newTd)
			# Convert TD to a number if possible, this
			# could be the serial number for a voter
			n = newTd.strip()
			try:
				n1 = int(n)
				#print 'Converted ', n
				slNo = n
			except ValueError:
				#print 'Unable to convert ', n
				pass
			# countDigs = reduce(lambda x,y: x+y, map(lambda x: x.isdigit()+0, '123'), 0)

		# Check if this is a serial number with the "R " or "# " form
		obj = slMatch.match(line)
		if obj:
			slNo = obj.groups()[0].strip()
			#if slNo.startswith('#'):
				#slNo = slNo.split(' ')[1].strip()

		# Check if this is a voter card ID - i.e. EPIC number
		obj = rejMatch.match(line)
		#if not obj:
		#	obj = rejMatch2.match(line)
		#if not obj:
		#	obj = rejMatch3.match(line)
		if obj:
			rejNo = obj.groups()[0].strip()
			#print '%5s %10s %s'%(slNo, rejNo, prevTds[-2])
			# PDF file can contain stuff in unicode format
			# we can't deal with these yet.
			# If the slNo turns out to be None, then it is
			# probably in unicode - need to look these up in
			# the PDF file.
			# If the name is in unicode, then prevTds[-2]
			# will not contain the name, it will contain the slNo
			if slNo is None:
				slNo = 'U 0'
			# Store unique prefixes
			if rejNo[:3] not in prefixList:
				prefixList.append(rejNo[:3])
			voterList.append((slNo, rejNo, prevTds[-2].strip()))
			slNo = None

	def cmpIds(X,Y):
		x = X[0]
		y = Y[0]
		#print 'cmp ', x, y, '=',
		if not x[0].isdigit():
			if not y[0].isdigit():
				try:
					n1 = int(x[1:]) # x will be in format "R xx" or "# xx" or "#xx"
				except IndexError:
					print >> sys.stderr, "Failed for x = ", x
					sys.exit(1)
				try:
					n2 = int(y[1:])
				except IndexError:
					print >> sys.stderr, "Failed for y = ", y
					sys.exit(1)
				#print n1-n2
				return n1-n2
			else:
				#print '-1'
				return 1
		else:
			if not y[0].isdigit():
				#print '-1'
				return -1
			#print int(x)-int(y)
			return int(x)-int(y)

	# Sort the voter list
	voterList.sort(cmp = cmpIds)
	for (slNo, rejNo, name) in voterList:
		if name == slNo:
			name = '(Unicode encoded)'
		# Generate the booth location by taking the address, and skipping
		# everythin else after the first comma. Multiple booths will be at
		# the same address, and it's likely that the guys there don't know
		# what's the room number. Instead, they will use the booth number as
		# the room number.
		try:
			boothLoc =  boothKey[int(boothNo)].split(',')[0]
		except KeyError:
			boothLoc = "(unknown)"
		print >>outfile, '%s, %5s, %10s, %s, %s'%(boothNo, slNo, rejNo, name, boothLoc)

fnames = glob('conv/*.pdf')
fnames.sort()
outfileName = 'voterlist.csv'
outfile = open('voterlist.csv', 'w')
#fnames = ['conv/AC1540334.pdf']
for fname in fnames:
	#print fname
	dumpVoterList(outfile, fname)

# Dump prefixes
#pprint(prefixList)
