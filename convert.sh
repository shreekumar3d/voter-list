#!/bin/bash
# Voter list files contain text in encoded format, so
# can't just run 'strings' on them and extract data.
# These files contain 'FlateDecode'ed streams. We
# convert these to text. This allows us to then process 
# the text in them
#
# For this, we need pdfinflt.ps 
# wget http://svn.ghostscript.com/ghostscript/trunk/gs/toolbin/pdfinflt.ps
#
# I got some of this info from 
# http://j-b.livejournal.com/339214.html
#
mkdir converted
for f in ceo-files/AC*.pdf; 
do 
	echo $f; 
	fname=`echo $f | sed -e "s/ceo-files\///"`
	gs -- pdfinflt.ps ceo-files/$fname converted/$fname; 
done
