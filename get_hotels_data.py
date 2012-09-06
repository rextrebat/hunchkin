#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import pymongo
import pprint


conn = pymongo.Connection("localhost", 27017)
db = conn.hotelgenome

pp = pprint.PrettyPrinter(indent=4)


hotel_ids = [
        216622,
        151589,
        111554,
        235139,
        111189,
        131217,
        248471,
        213189,
        111964,
        202349,
        ]


for h_id in hotel_ids:
    hotel = db.hotels.find_one({"hotelId": h_id})
    desc = db.hotel_descs.find_one({"@hotelId": str(h_id)})
    pois = db.hotel_pois.find_one({"hotelId": h_id})
    print ">> HOTEL ID %s" % (str(h_id))
    print "------xxxxxxxxxxx-------"
    pp.pprint(hotel)
    pp.pprint(desc)
    pp.pprint(pois)
    print "------xxxxxxxxxxx-------"
