#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__appname__ = "[application name here]"
__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"
#__license__ = "GNU GPL 3.0 or later"

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# -- Code Here --
import csv


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(description=__doc__,
            version="%%prog v%s" % __version__)
    #parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
    # default=False, help="Increase verbosity")

    opts, args = parser.parse_args()

    infile = "ean_data/ActivePropertyList.txt"
    outfile = "out/property_index.csv"

# read file
    with open(infile) as f_in:
        with open(outfile, "w") as f_out:
            w = csv.writer(f_out, delimiter="|")
            w.writerow(("id", "name"))
            for p in csv.DictReader(f_in, delimiter="|"):
                p_name = p["Name"] + "," + p["City"] + "," + p["Country"]
                w.writerow((p["EANHotelID"], p_name))
