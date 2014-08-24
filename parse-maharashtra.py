import xml.etree.ElementTree as ET
import re
import math
from pprint import pprint
import sys
import codecs

def computeDataRegions(thisPage):
	tokens = thisPage.findall('.//TOKEN')

	reVoterId = re.compile('[A-Z].*[0-9]{6,}')
	reElector = re.compile("Elector's") # Words seem to be getting split in the PDF
	reRelative = re.compile("(Father|Husband|Mother)'s")
	reHouse = re.compile("House")
	rePhoto = re.compile("Photo")
	reAge = re.compile("Age")
	reSex = re.compile("Sex")
	reSerial = re.compile("[0-9]+")

	fields = [ reElector, reRelative, reHouse, rePhoto, reAge, reSex, reSerial, reVoterId ]
	fieldIds = range(len(fields))

	boxValues = [None]*len(fields)
	boxNodes = [None]*len(fields)

	valSerial = None
	valVoter = None

	rects = []

	pageTotal = 0

	# Demarcate the page into boxes that contain voter info
	for tok in tokens:
		content = tok.text
		# If the current text matches a pattern, then we'll
		# keep the text.  If a similar pattern repeats multiple
		# times, only the last one will remain. This case happens
		# with the numbers (serial number, age, maybe house no).
		# Luckily the serial number comes last in the list, but this
		# is a possible gotcha in this algorithm
		for check in zip(fieldIds,fields):
			obj = check[1].match(content)
			if obj:
				boxValues[check[0]] = obj.group()
				boxNodes[check[0]] = tok
				break
		idx = None
		try:
			idx = boxValues.index(None)
		except ValueError:
			pass
		if (idx >= 6) or (idx is None):
			xVal = []
			yVal = []
			for nv in boxNodes:
				if nv is None:
					continue
				x = float(nv.attrib['x'])
				y = float(nv.attrib['y'])
				w = float(nv.attrib['width'])
				h = float(nv.attrib['height'])
				xVal.append(x)
				xVal.append(x+w)
				yVal.append(y)
				yVal.append(y+h)

			boundingRect = [min(xVal), min(yVal), max(xVal), max(yVal)]
			rectDim = [ boundingRect[2]-boundingRect[0], boundingRect[3]-boundingRect[1]]
			rects.append(boundingRect)
			boxValues = [None]*len(fields)
			boxNodes = [None]*len(fields)
	return rects

def extractVoterInfo(textRect, textNodes, pageNo):

	v_tolerance = 1.0
	def cmpBoxFields(a, b):
		y1 = float(a.attrib['y'])
		y2 = float(b.attrib['y'])
		if math.fabs(y1-y2) > v_tolerance:
			if y1 < y2:
				return -1
			elif y1 > y2:
				return 1
		x1 = float(a.attrib['x'])
		x2 = float(b.attrib['x'])
		if x1 < x2:
			return -1
		elif x1 > x2:
			return 1
		return 0

	textNodes.sort(cmp=cmpBoxFields)

#	print '-------'
#	print textNodes[0].text,
#	prevTok = textNodes[0]
#	for tok in textNodes[1:]:
#		if float(tok.attrib['y'])>(float(prevTok.attrib['y'])+v_tolerance):
#			print 
#		print tok.text,
#		prevTok = tok
#	print
#	print '-------'

	reVoterId = re.compile('[A-Z].*[0-9]{6,}')
	reElector = re.compile("Elector's") # Words seem to be getting split in the PDF
	reRelative = re.compile("(Father|Husband|Mother)'s")
	reHouse = re.compile("House")
	rePhoto = re.compile("Photo")
	reAge = re.compile("Age")
	reSex = re.compile("Sex")
	reSerial = re.compile("[0-9]+")

	info = {}

	info['page'] = pageNo

	# First item in the list needs to be the serial number
	ob = reSerial.match(textNodes[0].text)
	if ob:
		info["serial"] = ob.group()
		textNodes.pop(0)
	else:
		# If the first item is not a serial number, then
		# try to find the EPIC number and roll back by one
		#
		# Inability to find the serial number is mostly to do
		# with data that creeps into the box by virtue of 
		# landing up inside the box...
		#
		idx = 1
		while True:
			#print 'considering :',textNodes[idx].text
			ob = reVoterId.match(textNodes[idx].text)
			if ob:
				#print 'matched'
				idx = idx - 1
				break
			idx = idx + 1
			if idx == len(textNodes):
				print '!!! ERROR - reached end of list'
				return None
		ob = reSerial.match(textNodes[idx].text)
		if ob:
			info["serial"] = ob.group()
			#print info["serial"]
			for i in range(idx+1):
				textNodes.pop(0)
		else:
			#print textNodes[0].text
			# possibly raise an error
			#raise RuntimeError, "First item in rect needs to be serial"
			print '!!! ERROR - did not find serial no'
			return None

	# Next item is the EPIC number. This may be missed in
	# some nodes!
	info["epic"] = None
	ob = reVoterId.match(textNodes[0].text)
	if ob:
		info["epic"] = ob.group()
		textNodes.pop(0)

	# Filter out certain keywords that will not make it into the data
	textNodes = filter(lambda x: x.text not in ['Name',':','No.', 'Photo','Not', 'Available' ], textNodes)

	appendTo = None
	info["name"] = ""
	info["relative"] = ""
	info["residence"] = ""
	info["age"] = ""
	info["sex"] = ""

	appendTo = None
	for node in textNodes:
		content = node.text
		nodeChanged = False
		for tryMatch in zip(['name','relative','residence','age','sex'], [reElector, reRelative, reHouse, reAge, reSex]):
			ob = tryMatch[1].match(content)
			if ob:
				appendTo = tryMatch[0]
				nodeChanged = True
				if tryMatch[0] == 'relative':
					info["relation"] = ob.groups()[0]
				break
		if (not nodeChanged) and (appendTo is not None):
			info[appendTo] =( '%s %s'%(info[appendTo], content)).strip()
	#print info
	return info

def getVoterInfo(thisPage, rects, pageNo):
	def pointInRect(x, y, r):
		eps = 0.1
		if x<(r[0]-eps):
			return False
		if y<(r[1]-eps):
			return False
		if x>(r[2]-eps):
			return False
		if y>(r[3]-eps):
			return False
		return True

	tokens = thisPage.findall('.//TOKEN')

	voterInfo = []
	for thisRect in rects:
		# Figure out all the text nodes that belong to
		# this rect
		thisRectNodes = []
		for tok in tokens:
			x = float(tok.attrib['x'])
			y = float(tok.attrib['y'])
			w = float(tok.attrib['width'])
			h = float(tok.attrib['height'])
			if pointInRect(x,y, thisRect) or pointInRect(x+w, y+h, thisRect):
				thisRectNodes.append(tok)	

		# 
		info = extractVoterInfo(thisRect, thisRectNodes,pageNo)
		if info is not None:
			voterInfo.append(info)
	return voterInfo

doc = ET.parse('indented-vl-eng.xml')
root = doc.getroot()
pages = root.findall('PAGE')

voterInfo = []
for pageInfo in zip(range(len(pages)),pages):
	rects = computeDataRegions(pageInfo[1])
	#print 'Info about %d voters is in page %d'%(len(rects),pageInfo[0]+1)
	vInfo = getVoterInfo(pageInfo[1], rects, pageInfo[0]+1)
	if len(vInfo)>0:
		voterInfo.extend(vInfo)

fname = 'voterlist.csv'
print 'Writing data for %d voters to %s'%(len(voterInfo), fname)

f= codecs.open(fname,'w','utf-8')
for vInfo in voterInfo:
	#pprint(vInfo)
	print >>f,'%s,%s,%s,%s,%s,%s,%s,%s,%s'%(vInfo['page'],vInfo["serial"],vInfo["epic"],vInfo["name"],vInfo['relation'],vInfo["relative"],vInfo['residence'],vInfo["sex"],vInfo["age"])

f.close()
