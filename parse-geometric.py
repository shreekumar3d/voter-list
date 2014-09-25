#!/usr/bin/python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import re
import math
from pprint import pprint
import sys
import codecs
import argparse
import sys
import string
from copy import copy,deepcopy
import os
import glyphmapper
import os.path
from glob import glob

config = {}

def loadConfig():
	global config
	ign = {}
	execfile('config.py', ign, config)

def getConfig(filename, lang):
	filename = os.path.basename(filename)
	filename = filename.replace('.xml','')
	global config
	# start off with defaults
	retval = copy(config['default'])
	# Apply overrides
	try:
		thisOverride = config['override'][filename]
		for kv in thisOverride.keys():
			retval[kv] = thisOverride[kv]
	except:
		pass

	try:
		retval['lang'] = config['langConfig'][lang]
	except KeyError, e:
		print >>sys.stderr, "Unsupported language: %s"%(lang)
		sys.exit(-1)
	return retval

def findRects(groups, minW, maxW, minH, maxH):
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
			if w > minW and w < maxW and h > minH and h < maxH:
				rects.append([x1, y1, x2, y2])

	# Extract lines from the 2 point GROUP that satisfy our size
	# requirements, and are horizontal OR vertical.
	#
	# Each line [x1,y1,x2,y2] is stored such that
	#       x1<=x2 and y1<=y2
	#
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
				if l>minH and l<maxH:
					if y1<y2:
						vlines.append([x1,y1,x2,y2])
					else:
						vlines.append([x1,y2,x2,y1])
			if y1 == y2:
				l = math.fabs(x2-x1)
				if l>minW and l<maxW:
					if x1<x2:
						hlines.append([x1,y1,x2,y2])
					else:
						hlines.append([x2,y1,x1,y2])

	# Vertical sort function, based on Y
	def sortV(l1, l2):
		if l1[1]<l2[1]:
			return -1
		elif l1[1]>l2[1]:
			return 1
		return 0

	# Sort lines by Y. This will help the next phase.
	hlines.sort(cmp=sortV)
	vlines.sort(cmp=sortV)

	# Coordinate value tolerance based match.
	def coordMatch(v1, v2):
		if math.fabs(v1-v2)<0.5:
			return True
		return False

	# Combine the lines to create rectangles where possible.
	# A rectangle needs 2 horiz and 2 vert lines
	#
	# We start with a horizontal line (hcand1). Next, we find
	# an attachable vertical line vcand1. hcand2 is then chosen
	# to fit vcand1. vcand2 is chosen to attach to hcand2 and
	# hcand1.
	#
	#          hcand1
	#    +-----------------------+
	#    |                       |
	#  v |                       |v
	#  c |                       |c
	#  a |                       |a
	#  n |                       |n
	#  d |                       |d
	#  1 |                       |2
	#    +-----------------------+
	#          hcand2
	#
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
				if coordMatch(hcand2[2], vl[2]) and coordMatch(hcand2[3], vl[3]) and coordMatch(vl[0], hcand1[2]) and coordMatch(vl[1], hcand1[3]):
					vcand2 = vl
					break
		if vcand2:
			rects.append([hcand1[0], hcand1[1], hcand2[2], hcand2[3]])
			hlines.remove(hcand2)
			vlines.remove(vcand1)
			vlines.remove(vcand2)
		hlines.remove(hcand1)

	return rects

def computeDataRegions(filename, cfg, thisPage):
	# Every page has a xi:include attribute at the end of the page
	# This includes a vector XML file. The XML file contains lines and 
	# rectangles. 
	#
	# pdf2xml conversion results in this being stored in 
	# the <filename>_data directory.
	#
	# We use this vector file to load rectangles (5 point GROUP).
	#
	# The rectangles that are close to our target box size (with some
	# fuzz) are retained.
	#
	# Line GROUPs in the vector file are taken.  Lines that are
	# horizontal OR vertical and satisfy the target box size requirements
	# are retained.  Out of these, rectangles are created where possible.
	#
	# The rectangles from the 5 point GROUP and the 2 point GROUP are
	# the final rectangles that are considered to contain voter data.
	#
	shapeFileName = thisPage.getchildren()[-1].attrib['href']
	try:
		doc = ET.parse(os.path.join(os.path.dirname(filename), shapeFileName))
	except:
		# maybe the path in the file is OK
		doc = ET.parse(shapeFileName)
	root = doc.getroot()
	groups = root.findall('GROUP')

	minW = cfg['infoBoxWidthRange'][0]
	maxW = cfg['infoBoxWidthRange'][1]
	minH = cfg['infoBoxHeightRange'][0]
	maxH = cfg['infoBoxHeightRange'][1]

	rectsVoter = findRects(groups, minW, maxW, minH, maxH)
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
	rectsVoter.sort(cmp=cmpRects)
	return rectsVoter

def getNodeRect(node):
	x = float(node.attrib['x'])
	y = float(node.attrib['y'])
	w = float(node.attrib['width'])
	h = float(node.attrib['height'])
	return [x, y, x+w, y+h]

def nodesInRect(nodes, rect):
	ret = []
	for node in nodes:
		x1, y1, x2, y2 = getNodeRect(node)
		if pointInRect(x1,y1, rect):
			ret.append(node)
	return ret

def getRect(cfg, textRect, label):
	box = deepcopy(cfg[label])
	trWidth = textRect[2]-textRect[0]
	trHeight = textRect[3]-textRect[1]
	box[0] = textRect[0] + box[0]*trWidth
	box[1] = textRect[1] + box[1]*trHeight
	box[2] = textRect[0] + box[2]*trWidth
	box[3] = textRect[1] + box[3]*trHeight
	return box

def extractNodesIn(cfg, textRect, label, textNodes):
	if label is None:
		labelBox = textRect
	else:
		labelBox = getRect(cfg, textRect, label)
	passNodes = nodesInRect(textNodes, labelBox)
	failNodes = filter(lambda x:x not in passNodes, textNodes)
	return passNodes, failNodes

def createRectWH(rect):
	return [rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1]]

def arrangeTextBoxesInOrder(cfg, textNodes): 
	v_tolerance = cfg['lineSeparation']
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

def unicodeLookup(font, text, ignoreErrors):
	try:
		outs = u""
		for ch in text:
			if ord(ch)>=0xE000:
				outs += unichr(ord(ch)-0xE000)
			else:
				outs += ch
		#for ch in outs:
		#	print "%03x"%(ord(ch)),
		#print "=> "
		nodeText = lookahead[font].lookup(outs)
	except Exception, e:
		if ignoreErrors:
			nodeText =  "<Fail conversion>"
		else:
			raise e
	return nodeText

def extractText(cfg, textNodes):
	if len(textNodes)==0:
		return ''
	retVal = textNodes[0].text
	font = textNodes[0].attrib['font-name']

	for node in textNodes[1:]:
		retVal += node.text

	if type(retVal) is str:
		return retVal
	else:
		return unicodeLookup(font, retVal, False)

def extractVoterInfo(cfg, textRect, textNodes, pageNo, debugMatch):
	if len(textNodes) == 0:
		return None
	v_tolerance = cfg['lineSeparation']
	arrangeTextBoxesInOrder(cfg, textNodes)

	# Do unicode conversion back from glyphs if necessary
	for node in textNodes:
		global lookahead
		if type(node.text) is str:
			nodeText = node.text
		else:
			nodeText = unicodeLookup(node.attrib['font-name'],node.text, True)
		node.text2 = nodeText

	boxTextNodes = copy(textNodes)

	#reRelative = re.compile("(Father|Husband|Mother)'s")
	reRelative = cfg["lang"]["reRelative"]
	rePhoto = re.compile("Photo")
	#reSex = re.compile("Sex")
	reSex = cfg["lang"]["reSex"]

	info = {}

	info['page'] = pageNo
	info["name"] = ""
	info["relative"] = ""
	info["relation"] = ""
	info["residence"] = ""
	info["age"] = ""
	info["sex"] = ""

	infoKeys = info.keys()
	info["debug"] = {}
	for k in infoKeys:
		info['debug'][k] = []
	info['debug']['rejected'] = []
	info['debug']['leftRect'] = []
	info['debug']['rightRect'] = []

	snNodes, textNodes = extractNodesIn(cfg, textRect, 'snBox', textNodes)
	snText = extractText(cfg, snNodes)
	if len(snText)>10:
		print '!!! ERROR - invalid serial : %s'%(serial)
		return None
	info['serial'] = snText

	# Next item is the EPIC number. This may be missed in
	# some nodes!
	epicNodes, textNodes = extractNodesIn(cfg, textRect, 'epicBox', textNodes)
	info["epic"] = ""
	if len(epicNodes)>0:
		epic = extractText(cfg, epicNodes)
		if len(epic)>30:
			print '!!! ERROR - invalid EPIC : %s'%(epic)
			return None
		info['epic'] = epic

	# Find all nodes with a colon with them.
	# These will be for Name, relative's name, House No, Age and Sex
	colonNodes = filter(lambda x: x.text2.find(':')>=0, textNodes)
	if len(colonNodes)!=5:
		print '!!! ERROR - colon logic failed. Number of colonNodes = %d, expected 5'%(len(colonNodes))
		return None

	# Name's text will start below the SN box, ie the max Y
	snRect = getRect(cfg, textRect, "snBox")
	lastY = snRect[3]
	
	# Handle name, relative and residence
	fieldOrder = ['name','relative','residence']
	for node, field in zip(colonNodes[:3],fieldOrder):
		cnRect = getNodeRect(node)
		# Negative correction to ensure that end of rectangle is 
		# closer to baseline of text. Note that the text size _may_
		# vary between the colonNodes, so we have to compute this
		# from the colon node
		baseLine =  cnRect[1]+((cnRect[3]-cnRect[1])*0.5)
		# left of colon
		leftRect = [textRect[0], lastY, cnRect[2], baseLine]
		# right of colon. NOTE: the colon could be embedded, e.g.
		# as in the house no nodes
		rightRect = [cnRect[2], lastY, textRect[2], baseLine]
		lastY = baseLine
		info['debug']['leftRect'].append(createRectWH(leftRect))
		info['debug']['rightRect'].append(createRectWH(rightRect))
		leftNodes, textNodes = extractNodesIn(cfg, leftRect, None, textNodes)
		rightNodes, textNodes = extractNodesIn(cfg, rightRect, None, textNodes)
		arrangeTextBoxesInOrder(cfg, leftNodes)
		leftText = extractText(cfg, leftNodes)
		arrangeTextBoxesInOrder(cfg, rightNodes)
		rightText = extractText(cfg, rightNodes)
		fullText = leftText + rightText
		parts = fullText.split(':')
		info[field] = parts[1]

		if field == 'relative':
			ob = reRelative.match(parts[0])
			if ob:
				info["relation"] = ob.groups()[0]

	# Next, process Age and Sex
	remainingRect = [textRect[0], lastY, textRect[2], textRect[3]]
	ageSexNodes, textNodes = extractNodesIn(cfg, remainingRect, None, textNodes)
	if len(textNodes)>0:
		print '!!! ERROR: No nodes should remain after age & sex have been extraced'
		return None
	# Get the age & sex text
	arrangeTextBoxesInOrder(cfg, ageSexNodes)
	ageSexText = extractText(cfg, ageSexNodes)
	parts = ageSexText.split(':')
	# Sex is everything after second colon
	info['sex'] = parts[2]
	# And, age is everything between the first colon and
	# the start of the sex token 
	ageCandidate = parts[1]+':'+parts[2]
	sexNode = filter(lambda x: reSex.match(x.text2), ageSexNodes)[0]
	sexIdx = ageCandidate.find(sexNode.text2)
	if sexIdx > -1:
		info['age'] = ageCandidate[:sexIdx]

	if debugMatch(pageNo, info['epic']):
		print 'Matching record at page %3d'%(pageNo)
		indent = '  '
		print indent,
		print boxTextNodes[0].text2,
		prevTok = boxTextNodes[0]
		for tok in boxTextNodes[1:]:
			if float(tok.attrib['y'])>(float(prevTok.attrib['y'])+v_tolerance):
				print 
				print indent,
			try:
				print u"'%s'"%(tok.text2),
			except:
				print 'Unicode',
			prevTok = tok


		print
		print 'Output for record:'
		pprint(info)

	# Remove extra spaces
	for field in ['name', 'relative', 'relation', 'residence', 'age', 'sex']:
		info[field] = info[field].strip()

	#print info
	return info

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

def getVoterInfo(cfg, thisPage, rects, pageNo, debugMatch):
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
		info = extractVoterInfo(cfg, thisRect, thisRectNodes,pageNo, debugMatch)
		if info is not None:
			voterInfo.append(info)
	return voterInfo

#
# Script execution starts here...
#

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str, help="file to process")
parser.add_argument("--output", type=str, help="Write results to this file, defauts to voterlist.csv")
parser.add_argument("-e", "--epic", type=str, help="EPIC number filter, use with debugging")
parser.add_argument("-p", "--page", type=int, help="Page number, use with debugging")
parser.add_argument("-s", "--source-pdf", type=str, help="Use this source PDF file for annotation. This will typically be the original source for the XML file.")
parser.add_argument("-d", "--debug", help="Generate debug information. If both 'epic' and 'page' are specified, then match both. If both are not given, then all records are dumped.  If only one is specified, then only that aspect is matched.", action="store_true")
parser.add_argument("-l", "--language", type=str, help="Specify that voter information in the file is in this language.", required=True)
args = parser.parse_args()

# Default to voterlist.csv if no other filename is given
if not args.output:
	args.output = 'voterlist.csv'

# Parse document, find all pages
print '%s => %s ...'%(args.filename, args.output)
print 'Using language %s.'%(args.language)
sys.stdout.flush()

doc = ET.parse(args.filename) #'indented-vl-eng.xml'
root = doc.getroot()
pages = root.findall('PAGE')

loadConfig()
cfg = getConfig(args.filename, args.language)

voterInfo = []

def debugMatch(pageNo, epic):
	if not args.debug:
		return False

	# debug all ?
	if (args.epic is None) and (args.page is None):
		return True

	if (args.epic is not None) and (args.page is not None):
		if (args.epic == epic) and (args.page == pageNo):
			return True
		return False

	if (args.epic is not None) and (args.epic == epic):
		return True

	if (args.page is not None) and (args.page == pageNo):
		return True

	return False

lookahead = {}
for filename in glob('data/*.glyphmap'):
	fontname = os.path.basename(filename)
	fontname = fontname.replace('.glyphmap','')
	print 'Loading %s...'%(filename)
	lookahead[fontname] = glyphmapper.loadDirect(filename)

# For each page, figure out the rects that
# contain voter info, then extract data
# from each.
for pageInfo in zip(range(len(pages)),pages):
	pageNo = pageInfo[0]+1
	# Skip pages if debug page filter is active
	if args.debug and (args.page is not None):
		if pageNo != args.page:
			continue
	rects = computeDataRegions(args.filename, cfg, pageInfo[1])
	#print 'Info about %d voters is in page %d'%(len(rects),pageInfo[0]+1)
	vInfo = getVoterInfo(cfg, pageInfo[1], rects, pageNo, debugMatch)
	if len(vInfo)>0:
		voterInfo.extend(vInfo)

print 'Total %d records.'%(len(voterInfo))

f= codecs.open(args.output,'w','utf-8')

sep = '|' # field separator

fieldOrder = ['page', 'serial', 'epic', 'name', 'age', 'sex', 'relation', 
              'relative', 'residence' ]
print >>f, string.join(fieldOrder, sep)

for vInfo in voterInfo:
	values = map(lambda fieldName: vInfo[fieldName], fieldOrder)
	values[0] = str(values[0]) # Convert page number to string
	print >>f, string.join(values, sep) 

f.close()

def createRect(r, x, y, w, h, style):
	attribs = {
		'style':style,
		'd':"M %f %f L %f %f L %f %f L %f %f L %f %f"%(x, y, x+w, y, x+w, y+h, x, y+h, x, y) }
	rect = ET.SubElement(r, 'ns0:path', attribs)
	return rect

if (args.debug is not None) and (args.page is not None) and (args.source_pdf is not None):
	output = 'debug.svg'
	print 'Creating %s for page %d ...'%(output, args.page)
	os.system("pdf2svg %s %s %d"%(args.source_pdf, output, args.page))
	svgDoc = ET.parse(output)
	svgRoot = svgDoc.getroot()
	for vInfo in voterInfo:
		debugInfo = vInfo['debug']
		for kv in debugInfo.keys():
			try:
				print 'style for :', kv, ' is ',
				style = cfg['style'][kv]
			except:
				style = cfg['style']['default']
			print style
			for rect in debugInfo[kv]:
				createRect(svgRoot, rect[0],rect[1],rect[2],rect[3], style)
	svgDoc.write(output)
