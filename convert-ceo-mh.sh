#!/bin/bash
#
# Convert voter lists in ceo-mh/pdf directory to
# XML format in ceo-mh/converted directory. These
# XML files can then be processed by pdftoxml
#
# Assumes that pdftoxml.exe is in PATH.
#

pdftoxml.exe -v 2>/dev/null
# pdftoxml returns a -99 !!
if test "$?" != "99"; then 
	echo "pdftoxml.exe is not in PATH. I need it!"
	exit 1
fi

mkdir ceo-mh/converted
for f in ceo-mh/pdf/*.pdf; 
do 
	fname=`echo $f | sed -e "s/\/pdf\//\/converted\//" | sed -e"s/.pdf$/.xml/"`
	echo "$f => $fname"; 
	pdftoxml.exe $f $fname; 
done
