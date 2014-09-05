voter-list
==========

Scripts to process voter lists in PDF format. Voter lists with
indic chars in them are not handled yet. Only english voter
lists work as expected. And even then, YMMV.

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

After this, there are two methods to process the files.

### New Method ###

This method uses pdf2xml to process the PDF file, followed by
geometric methods to determine the data.

First, you need to run pdftoxml.  For Windows users, precompiled
binaries are included in precompiled-binaries/win32/

    $ pdftoxml ceo-files/AC1540310.pdf converted/AC1540310.xml

This converts the source PDF file into an XML representation. You
will see an additional directory "AC1540310.xml_data" in the "converted"
direction.  This contains files referenced in the xml.

    $ ./parse-geometric.py converted/AC1540310.xml

This will generate voterlist.csv.  Note: csv file has pipe symbol (|)
as separator. This is necessary due to usage of the comma in address
field.

After this is done, have a look at the generated voterlist.csv. It may
be necessary to tweak config.py to use slightly different values...

#### Debug Information ####

parse-geometric can dump information about it's internal processing.
This can be used to fine-tune parameters, as well as to understand what
is happening behind the scenes.

This is activated via the -d option.

To understand processing for epic REJ5021886, you might use:

    $ ./parse-geometric.py -d -e REJ5021886 converted/AC1540347.xml

This will dump info about all voter records for REJ5021886 in the file.
(Note: there may be more than one. We don't differentiate among the
multiple records _yet_)

To specify a specific page, use the page option "-p". This will dump
all records in the specified page.

If both epic and page are given, then a specific record only is dumped,
and that only if it exists. 

The script will not warn if no records match in debug mode. If you see 
no output, please check params!a

If you don't give any of -p or -d options, then debug info will be
dumped for all records!

### Earlier Method ###

This method relies on the relative ordering of data in PDF files. This
was hurriedly cooked up by Shree earlier, and is not a robust method.
Not recommended for use.

Convert the PDF into a "decoded text" form

    $ ./convert.sh

This will create a directory "converted" with equivalent PDF files
that contain decoded text.

Next, generate the list

    $ ./extract-voter-info 

This will save the voter list in the file 'voterlist.csv'

Searching
-----

PS: It would be really nice to make apps of various types
that use the data.

Search with good-ol-grep ! You can search by name or
EPIC number

    $ grep REJXXXXXXX voterlist.csv

Multiple matches, fuzzy matches, creative matches, match by
relative, etc can next be done.  Also, you may run grep on the
files in the "conv" directory - another powerful way to query.
