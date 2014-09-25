# -*- coding: utf-8 -*-
import json
import os
from pprint import pprint
import codecs
import cPickle as pickle

class MyDict(dict):
	def __getitem__(self, key):
		try:
			return dict.__getitem__(self, key)
		except KeyError:
			return None
	def has_key(self, key):
		return dict.has_key(self, key)

class LookaheadUnicodeExtractor():
	def __init__(self):
		self.root = MyDict()
		self.root['special'] = {
			' ' : None
		}
	def add(self, glyphSequence, equivalentUnicode):
		curRoot = self.root
		for glyph in glyphSequence:
			if not curRoot.has_key(glyph):
				d = MyDict()
				d['value'] = None
				curRoot[glyph] = d
			curRoot = curRoot[glyph]
		curRoot['value'] = equivalentUnicode
		if equivalentUnicode in self.root['special'].keys():
			print "Special for '%s'='%s'"%(equivalentUnicode, glyphSequence)
			self.root['special'][equivalentUnicode] = glyphSequence

	def getSpecial(self, uc):
		return self.root['special'][uc]

	def lookupSingle(self, glyphSequence):
		lookupResult = None

		# Choose the start node
		curRoot = self.root[glyphSequence[0]]

		lookupLength = 0
		totalLength = 1

		for glyph in glyphSequence[1:]:
			if curRoot is None:
				return (lookupResult, lookupLength)

			# this nodes value is good for now
			if curRoot['value'] is not None:
				lookupResult = curRoot['value']
				lookupLength = totalLength

			# traverse to the next node
			curRoot = curRoot[glyph]

			# We've processed one more char		
			totalLength += 1

		# process the last char
		if curRoot and (curRoot['value'] is not None):
			lookupResult = curRoot['value']
			lookupLength = totalLength

		return (lookupResult, lookupLength)

	def lookup(self, glyphSequence):
		idx = 0
		result = u""
		while idx < len(glyphSequence):
			partialResult, consumedLen = self.lookupSingle(glyphSequence[idx:])
			if not partialResult:
				msg =  u"Unable to convert, error at %s, position %d"%(glyphSequence, glyphSequence[idx:], idx)
				raise ValueError(msg)
			idx += consumedLen
			result += partialResult
		return result

	def save(self, filename):
		f = open(filename, 'wb')
		f.write(pickle.dumps(self.root))
		f.close()

	def load(self, filename):
		f = open(filename, 'rb')
		self.root = pickle.loads(f.read())
		f.close()

def loadDirect(filename):
	lookahead = LookaheadUnicodeExtractor()
	lookahead.load(filename)
	return lookahead

def loadMapping(unicodeFileName, glyphFileName):
	decoder = json.JSONDecoder()

	unicodeFile = codecs.open(unicodeFileName, 'r', 'utf-8')
	glyphFile = codecs.open(glyphFileName, 'r')

	lookahead = LookaheadUnicodeExtractor()
	for unicodeLine,glyphLine in zip(unicodeFile.readlines(), glyphFile.readlines()):
		unicodeLine = unicodeLine[:-1] # Strip newline
		glyphList = decoder.decode(glyphLine)
		glyphLine = u""
		for glyph in glyphList:
			glyphLine += unichr(glyph['id'])
		lookahead.add(glyphLine, unicodeLine)
	return lookahead

if __name__ == '__main__':
	lookahead = loadMapping("kn-unicode-combinations.txt",
 	                        "kn-glyph-combinations.txt")
	inf = codecs.open("glyph.txt", "r", "utf-8")
	outf = codecs.open('out.txt', 'w', 'utf-8')
	# Shree
	lookupStr = inf.read()	
	result = lookahead.lookup(lookupStr)
	#print 'Output: ',
	#for ch in result:
	#	print '%03x'%(ord(ch)),
	#print
	print >>outf, result
