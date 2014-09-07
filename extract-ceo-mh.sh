#!/bin/bash
mkdir ceo-mh/csv
for f in ceo-mh/converted/A*.xml; 
do 
	fname=`echo $f | sed -e "s/\/converted\//\/csv\//" | sed -e"s/.xml$/.csv/"`
	./parse-geometric.py --output=$fname $f; 
done
