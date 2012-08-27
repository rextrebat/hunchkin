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


offsets = [11, 121, 253]
hotels = db.hotels.find({}, {"hotelId":1})
hotel_ids = [hotels[o]["hotelId"] for o in offsets]

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
