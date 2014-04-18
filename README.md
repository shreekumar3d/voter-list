voter-list
==========

Scripts to process voter lists in PDF format.

Usage
-----

First, get some files from the electoral rolls:
(This will take some time, as the files need to be fetched
from the internet.)

    $ ./get-voterlists.py 154 310 348

Here :
    - 154 is the AC number
    - (310, 338) is the booth range.
    - The range for this full constituency is (1,348) - approx
      5 MB every file.

The voter lists are fetched to the directory 'ceo-files'.

Next, convert the PDF into a "decoded text" form

    $ ./convert.sh

This will create a directory "converted" with equivalent PDF files
that contain decoded text.

Next, generate the list

    $ ./extract-voter-info 

This will save the voter list in the file 'voterlist.csv'

Next, search with good-ol-grep ! You can search by name or
EPIC number

    $ grep REJXXXXXXX voterlist.csv

Multiple matches, fuzzy matches, creative matches, match by
relative, etc can next be done.  Also, you may run grep on the
files in the "conv" directory - another powerful way to query.
