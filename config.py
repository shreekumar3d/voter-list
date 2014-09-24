# -*- coding: utf-8 -*-
#
# Configuration file for processing XML files.
# 
#
# This file is loaded by parse-geometric.py
#


#
# Defaults. Note that the name "default" is 
# used in the script, and must not be changed.
#
default = {
	# Voter info is kept in boxes, typically
	# 3 boxes fit in a page size.
	# infoBoxWidthRange and infoBoxHeightRange
	# give a range of dimensions of the box.
	# The dimensions are in "points"
	'infoBoxWidthRange' : [170, 190],
	'infoBoxHeightRange' : [60, 80],
	# Text in each box can be haphazardly aligned
	# Text that is offset by as much as 'lineSeparation'
	# points is treated as a continuous string...
	'lineSeparation' : 2.0,

	'style': { 
		'default':"fill:none;stroke:#ff0000;stroke-opacity:0.2",
		'leftRect':"fill:none;stroke:#00ff00;stroke-opacity:1",
		'rightRect':"fill:none;stroke:#0000ff;stroke-opacity:1",
	}
}

# Start off with no overrides. Do not change the
# name of this variable
override = {}

# Start defining overrides. 
# Override key is the filename, without extension
# Unspecified values are used from the default
# e.g.
override['AC1540310'] = { 'lineSeparation' : 2.0 }

override['AC2080142'] = {
	'snBox' : [ 0, 0, 0.25, 0.2 ],
	'epicBox' : [0.25, 0, 1.0, 0.2],
}
