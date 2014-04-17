voter-list
==========

Scripts to process voter lists in PDF format.

Usage
-----

First, get some files from the electoral rolls:

    $ ./get-voterlists.py 154 338 338

Here :
    - 154 is the AC number
    - (338, 338) is the booth range.

Next, convert the PDF into a "decoded text" form

    $ ./convert.sh

Next, generate the list

    $ ./extract-voter-info > voter-list.csv

Next, search with good-ol-grep ! You can search by name or
EPIC number

    $ grep REJXXXXXXX voter-list.csv
