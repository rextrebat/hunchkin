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

room_amenities = {}
property_amenities = {}

cur = db.hotel_descs.find()

for h in cur:
    if "RoomTypes" in h and "RoomType" in h["RoomTypes"]:
        room_types = h["RoomTypes"]["RoomType"]
        if type(room_types) != list:
            room_types = [room_types]
        for r in room_types:
            if "roomAmenities" in r and "RoomAmenity" in r["roomAmenities"]:
                amenities = r["roomAmenities"]["RoomAmenity"]
                if type(amenities) != list:
                    amenities = [amenities]
                for a in amenities:
                    if a["amenity"].strip() not in room_amenities:
                        room_amenities[a["amenity"].strip()] = None

    if "PropertyAmenities" in h and "PropertyAmenity" in h["PropertyAmenities"]:
        prop_amenities = h["PropertyAmenities"]["PropertyAmenity"]
        if type(prop_amenities) != list:
            prop_amenities = [prop_amenities]
        for a in prop_amenities:
            if a["amenity"].strip() not in property_amenities:
                property_amenities[a["amenity"].strip()] = None

print "ROOM AMENITIES"
print "--------------"
for k in room_amenities.iterkeys():
    print "%s" % (k.encode("ascii", "replace"))
print "---------------------------------------------------------------------"

print "PROPERTY AMENITIES"
print "------------------"
for k in property_amenities.iterkeys():
    print "%s" % (k.encode("ascii", "replace"))
print "---------------------------------------------------------------------"
