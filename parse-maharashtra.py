import xml.etree.ElementTree as ET
import re
import math
from pprint import pprint
import sys
import codecs

def computeDataRegions(thisPage):
	# Every page has a xi:include attribute at the end of the page
	# This includes a vector XML file. The XML file contains lines and rectangles
	# the pdf2xml conversion results in this being stored in the filename_data directory
	# We use this vector file to load rectangles (5 point GROUPS)
	# The groups that are close to our target box size containing data are retained.  The rest are junked.
	shapeFileName = thisPage.getchildren()[-1].attrib['href']
	doc = ET.parse(shapeFileName)
	root = doc.getroot()
	groups = root.findall('GROUP')
	rects = []
	for g in groups:
		gc = g.getchildren()
		if len(gc)==5:
			xvals = map(lambda v:float(v.attrib['x']), gc)
			yvals = map(lambda v:float(v.attrib['y']), gc)
			x1 = min(xvals)
			y1 = min(yvals)
			x2 = max(xvals)
			y2 = max(yvals)
			w = x2-x1
			h = y2-y1
			if w > 170 and w < 190 and h > 60 and h < 80:
				rects.append([x1, y1, x2, y2])

	hlines = []
	vlines = []
	for g in groups:
		gc = g.getchildren()
		if len(gc)==2:
			xvals = map(lambda v:float(v.attrib['x']), gc)
			yvals = map(lambda v:float(v.attrib['y']), gc)
			x1 = xvals[0]
			y1 = yvals[0]
			x2 = xvals[1]
			y2 = yvals[1]
			if x1 == x2:
				l = math.fabs(y2-y1)
				if l>60 and l<80:
					if y1<y2:
						vlines.append([x1,y1,x2,y2])
					else:
						vlines.append([x1,y2,x2,y1])
			if y1 == y2:
				l = math.fabs(x2-x1)
				if l>170 and l<190:
					if x1<x2:
						hlines.append([x1,y1,x2,y2])
					else:
						hlines.append([x2,y1,x1,y2])
	def sortV(l1, l2):
		if l1[1]<l2[1]:
			return -1
		elif l1[1]>l2[1]:
			return 1
		return 0
	hlines.sort(cmp=sortV)
	vlines.sort(cmp=sortV)

	def coordMatch(v1, v2):
		if math.fabs(v1-v2)<0.5:
			return True
		return False

	while hlines:
		hcand1 = hlines[0]
		vcand1 = None
		hcand2 = None
		vcand2 = None
		# find a vertical line that starts at first corner
		for vl in vlines:
			if coordMatch(hcand1[0], vl[0]) and coordMatch(hcand1[1], vl[1]):
				vcand1 = vl
				break
		if vcand1:
			# find a horizontal line that starts at first corner
			for hl in hlines:
				if coordMatch(vcand1[2], hl[0]) and coordMatch(vcand1[3], hl[1]):
					hcand2 = hl
					break
		if hcand2:
			for vl in vlines:
				if coordMatch(hcand2[2], vl[2]) and coordMatch(hcand2[3], vl[3]):
					vcand2 = vl
					break
		if vcand2:
			rects.append([hcand1[0], hcand1[1], hcand2[2], hcand2[3]])
			hlines.remove(hcand2)
			vlines.remove(vcand1)
			vlines.remove(vcand2)
		hlines.remove(hcand1)

	def cmpRects(r1,r2):
		r1_y = r1[1]
		r2_y = r2[1]
		if r1_y < r2_y:
			return -1
		elif r1_y > r2_y:
			return 1
		r1_x = r1[0]
		r2_x = r2[0]
		if r1_x < r2_x:
			return -1
		elif r1_x > r2_x:
			return 1
		return 0
	# Sort with Y first, then X
	rects.sort(cmp=cmpRects)
	return rects

def extractVoterInfo(textRect, textNodes, pageNo):

	v_tolerance = 5.0
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

#	print 'Page %d -------'%(pageNo)
#	print textNodes[0].text,
#	prevTok = textNodes[0]
#	for tok in textNodes[1:]:
#		if float(tok.attrib['y'])>(float(prevTok.attrib['y'])+v_tolerance):
#			print 
#		try:
#			print tok.text,
#		except:
#			print 'Unicode',
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
		# keep adding till you find the number
		# This handles the case where there's an extra "(S)"
		# No idea what this stands for !
		serial = textNodes[0].text
		idx = 1
		while True:
			#print 'considering :',textNodes[idx].text
			ob = reSerial.match(textNodes[idx].text)
			if ob:
				#print 'matched'
				serial = serial + ' ' + textNodes[idx].text
				info['serial'] = serial
				idx = idx + 1
				break
			serial = serial + ' ' + textNodes[idx].text
			idx = idx + 1
			if len(serial)>10:
				print '!!! ERROR - invalid serial'
				return None
		for i in range(idx):
			textNodes.pop(0)

	# Next item is the EPIC number. This may be missed in
	# some nodes!
	info["epic"] = ""
	ob = reVoterId.match(textNodes[0].text)
	if ob:
		info["epic"] = ob.group()
		textNodes.pop(0)

	# Filter out certain keywords that will not make it into the data
	blacklist = ['Name',':','No.', 'Photo','Not', 'Available']
	textNodes = filter(lambda x: x.text not in blacklist, textNodes)
	outNodes = []
	for s in textNodes:
		s = s.text.strip()
		for token in blacklist:
			s = s.replace(token, '')
			s = s.strip()
		outNodes.append(s)
	textNodes = outNodes

	appendTo = None
	info["name"] = ""
	info["relative"] = ""
	info["relation"] = ""
	info["residence"] = ""
	info["age"] = ""
	info["sex"] = ""

	appendTo = "name" # By default after EPIC
	for content in textNodes:
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
			if pointInRect(x,y, thisRect):
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
	pageNo = pageInfo[0]+1
	if pageNo !=3 :
		continue
	rects = computeDataRegions(pageInfo[1])
	#print 'Info about %d voters is in page %d'%(len(rects),pageInfo[0]+1)
	vInfo = getVoterInfo(pageInfo[1], rects, pageNo)
	if len(vInfo)>0:
		voterInfo.extend(vInfo)

fname = 'voterlist.csv'
print 'Writing data for %d voters to %s'%(len(voterInfo), fname)

f= codecs.open(fname,'w','utf-8')
print >>f,"PageNo,SerialNo,EPIC,Name,Age,Sex,Relation,RelativeName,HouseInfo"

for vInfo in voterInfo:
	#pprint(vInfo)
	print >>f,'%s|%s|%s|%s|%s|%s|%s|%s|%s'%(vInfo['page'],vInfo["serial"],vInfo["epic"],vInfo["name"],vInfo["age"],vInfo["sex"], vInfo['relation'],vInfo["relative"],vInfo['residence'])

f.close()
