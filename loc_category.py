#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Location Categories"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
import csv

# ---GLOBALS

logger = logging.getLogger("loc_category")

#const for distance for categories
LOC_DIST = 2000

conn = None

conn_mongo = None

categories = {}

category_order = []


def read_categories(fname):
    """
    Read categories from file
    """
    global categories
    with open(fname) as f:
        for count, r in enumerate(csv.reader(f)):
            if count == 0:
                continue
            r = [c.strip() for c in r]
            place_type, category = r
            if category not in categories:
                categories[category] = []
            categories[category].append(place_type)


def get_category(place):
    """
    Return best fitting category for a given place
    """
    for c in category_order:
        for p_type in categories[c]:
            if p_type in place["types"]:
                return c
    return None


def save_loc_cat(h_id, loc_cat):
    """
    Save location categories to db
    """
    cursor = conn.cursor()
    loc_cat = [
            (h_id, cat, LOC_DIST, count) for cat, count \
                    in loc_cat.iteritems()
                    ]
    cursor.executemany(
            """
            INSERT INTO loc_categories
            (hotel_id, category, distance, count)
            VALUES
            (%s, %s, %s, %s)
            """, loc_cat)
    conn.commit()
    cursor.close()


def categorize_pois(h_id):
    """
    Get all pois for a hotel, find category for each and create dict with tally
    """
    loc_cat = {}
    for c in category_order:
        loc_cat[c] = 0
    db = conn_mongo.hotelgenome
    res = db.hotel_pois.find_one({'hotelId': h_id})
    if res:
        for p in res['places']:
            cat = get_category(p)
            if cat:
                loc_cat[cat] += 1
    return loc_cat


