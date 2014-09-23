#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import os
from copy import copy

# swaras start from 'a'
swaras = [ 
u"ಅ", u"ಆ", u"ಇ", u"ಈ", u"ಉ", u"ಊ", u"ಋ", u"ೠ",
u"ಎ", u"ಏ", u"ಐ", u"ಒ", u"ಓ", u"ಔ", u"ಅಂ", u"ಅಃ" 
]

#0xc85, 0xc86, 0xc87, 0xc88, 0xc89, 0xc8a, 0xc8b, 0xce0, 0xc8e, 0xc8f, 0xc90, #0xc92, 0xc93, 0xc94, 0xc95, 0xc85, 0xc82

# vyanjana
vyanjanas = [ 
u"ಕ", u"ಖ", u"ಗ", u"ಘ", 
u"ಚ", u"ಛ", u"ಜ", u"ಝ", 
u"ಟ", u"ಠ", u"ಡ", u"ಢ", u"ಣ",
u"ತ", u"ಥ", u"ದ", u"ಧ", u"ನ",
u"ಪ", u"ಫ", u"ಬ", u"ಭ", u"ಮ",
u"ಯ", u"ರ", u"ಲ", u"ವ", u"ಶ", u"ಷ",
u"ಸ", u"ಹ", u"ಳ"
]

matra_combinations = [ 
u"ಕ್", u"ಕ", u"ಕಾ", u"ಕಿ", u"ಕೀ", u"ಕು", u"ಕೂ", u"ಕ್ರು", u"ಕೃ", 
u"ಕೆ", u"ಕೇ", u"ಕೈ", u"ಕೊ", u"ಕೋ", u"ಕೌ", u"ಕಂ", u"ಕಃ" 
]
halant = matra_combinations[0][1:]

matra_append = []

for mc in matra_combinations:
	matra_append.append(mc[1:])

combinations = copy(swaras) 

# the ka-gunita
# this is what you learn in primary school
ka_gunita = []
for ch in vyanjanas:
	for append in matra_append:
		nextOne = ch+append
		ka_gunita.append(nextOne)

combinations += ka_gunita

# two vyanjanas followed by a swara
# note : this includes the arka stuff too
# as arka is just a combintaion of R followed
# by others e.g. ರ್ಕ್ => ರ್ + ಕ್
twocombo = []
for ch in vyanjanas:
	for append in ka_gunita:
		nextOne = ch+halant+append
		twocombo.append(nextOne)
combinations += twocombo

unicodeFileName = "kn-unicode-combinations.txt"
glyphFileName = "kn-glyph-combinations.txt"

punctuations = [ 
u"!", u"@", u"#", u"$", u"%", u"*", u"(", u")",
u"-", u"+", u"=", u";", 
u":", u'"', u"'", u",", u"<", u".", u">", u"?", u"/", u"{", u"[", u"}", 
u"]", u"\\" 
]

numbers = [ u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"0" ]
numbers += [u"೦", u"೧", u"೨", u"೩", u"೪", u"೫", u"೬", u"೭", u"೮", u"೯"] 

whitespace = [ u" ", u"\t" ]

combinations += punctuations
combinations += numbers
combinations += whitespace
 
outf = codecs.open(unicodeFileName, "w","utf-8") 	
for ch in combinations:
	print >>outf, ch
outf.close()

print "Converting to glyphs..."
os.system("../harfbuzz/util/hb-shape --text-file=%s --output-format=json --output-file=%s fonts/tunga.ttf"%(unicodeFileName, glyphFileName))
