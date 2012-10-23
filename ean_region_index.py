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


regions = {}


region_type = {
"City": "City",
"Continent": "Continent",
"Country": "Country",
"Multi-City (Vicinity)": "Multi-City",
"Multi-Region (within a country)": "Multi-Region",
"Neighborhood": "Neighborhood",
"Point of Interest": "POI",
"Point of Interest Shadow": "POI_Shadow",
"Province (State)": "State",
}



if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(description=__doc__,
            version="%%prog v%s" % __version__)
    #parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
    # default=False, help="Increase verbosity")

    opts, args = parser.parse_args()

    infile = "ean_data/ParentRegionList.txt"
    outfile = "out/region_index.csv"

# read file
    with open(infile) as f:
        for r in csv.DictReader(f, delimiter="|"):
            regions[r["RegionID"]] = r
    
# write output
    with open(outfile, "w") as f:
        w = csv.writer(f, delimiter="|")
        w.writerow(("id", "name", "type"))
        for r_id, r in regions.iteritems():
            t = r
            r_name = ""
            r_type = region_type[t["RegionType"]]
            if t["RegionType"] == "Continent":
                continue
            elif t["ParentRegionID"] == 0:
                continue
            while True:
                #r_name += " " + t["RegionNameLong"]
                r_name += " " + t["RegionName"]
                if t["RegionType"] == "Country":
                    break
                else:
                    next_id = t["ParentRegionID"]
                    if next_id not in regions:
                        break
                    else:
                        t = regions[next_id]
            w.writerow((r_id, r_name.strip(), r_type))
