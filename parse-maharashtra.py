import xml.etree.ElementTree as ET
import re
import math
from pprint import pprint
import sys

doc = ET.parse('indented-vl-eng.xml')
root = doc.getroot()
pages = root.findall('PAGE')
thisPage = pages[3]
tokens = thisPage.findall('.//TOKEN')

reVoterId = re.compile('[A-Z].*[0-9]{6,}')

reElector = re.compile("Elector's") # Words seem to be getting split in the PDF
reRelative = re.compile("(Father|Husband)'s")
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

infoGroups = []

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
		infoGroups.append([boundingRect, rectDim, boxValues, boxNodes, []])
		boxValues = [None]*len(fields)
		boxNodes = [None]*len(fields)

print 'Info about %d voters is in this page'%(len(infoGroups))
#for group in infoGroups:
#	print group[2]

#sys.exit(1)

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

for tok in tokens:
	x = float(tok.attrib['x'])
	y = float(tok.attrib['y'])
	w = float(tok.attrib['width'])
	h = float(tok.attrib['height'])
	for group in infoGroups:
		if pointInRect(x,y, group[0]):
			#if tok not in infoGroups[0][3]:
			group[4].append(tok)
			#content = tok.text
			#print "'%s'"%(content)
			# we're done
			break

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

for group in infoGroups:
	group[4].sort(cmp=cmpBoxFields)

#	for tok in group[4]:
#		print '%20s %10s %10s'%(tok.attrib['x'], tok.attrib['y'], tok.text)
#	
#	print
#
#	print group[4][0].text,
#	prevTok = group[4][0]
#	for tok in group[4][1:]:
#		if float(tok.attrib['y'])>(float(prevTok.attrib['y'])+v_tolerance):
#			print 
#		print tok.text,
#		prevTok = tok
#
#	print
#	print
#	print

#sys.exit(1)
for group in infoGroups:
	# Filter out certain keywords that will not make it into the data
	group[4] = filter(lambda x: x.text not in ['Name',':','No.', 'Photo','Available' ], group[4])

	# Fill out the data we already have
	info = {}

	serialInfo = group[3][6]
	info['serial'] = None
	if serialInfo is not None:
		info['serial'] = serialInfo.text
		group[4].remove(serialInfo)

	epicInfo = group[3][7]
	info['epic'] = None
	if epicInfo is not None:
		info['epic'] = epicInfo.text
		group[4].remove(epicInfo)

	# Create placeholders for data we will fill next
	info['name'] = ""
	info['relative'] = ""
	info['residence'] = ""
	info['age'] = ""
	info['sex'] = ""

	appendTo = None
	for tok in group[4]:
		details = group[3]
		if tok is details[0]:
			appendTo = 'name'
		elif tok is details[1]:
			appendTo = 'relative'
		elif tok is details[2]:
			appendTo = 'residence'
		elif tok is details[4]:
			appendTo = 'age'
		elif tok is details[5]:
			appendTo = 'sex'
		elif appendTo is not None:
			info[appendTo] =( '%s %s'%(info[appendTo], tok.text)).strip()

	print info
