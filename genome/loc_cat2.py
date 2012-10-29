#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Location Categories"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
import csv
import pymongo
import MySQLdb
from collections import Counter

# ---GLOBALS
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger("loc_category")

conn = MySQLdb.Connection(
    host="localhost",
    user="appuser",
    passwd="rextrebat",
    db="hotel_genome"
)

conn_mongo = pymongo.Connection()

categories = {}

DIST_BUCKETS = (1000, 5000)


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
            category, hk_category = r
            categories[category] = hk_category


def collect_category_data(h_id, dist_limit, places):
    """
    hotel_id: 
    dist: 
    places: list of category, distance
    """
    c = Counter()
    for p in places:
        cat, dist = p
        hk_cat = categories.get(cat, None)
        if hk_cat:
            if dist > 0 and dist <= dist_limit:
                c[hk_cat] += 1
    recs = [(h_id, dist_limit, hk_cat, cnt) for hk_cat, cnt in c.iteritems()]
    return recs


def save_loc_cat(recs):
    """
    Save location categories to db
    """
    cursor = conn.cursor()
    cursor.executemany(
            """
            INSERT INTO loc_categories
            (hotel_id, distance, category, count)
            VALUES
            (%s, %s, %s, %s)
            """, recs)
    conn.commit()
    cursor.close()


if __name__ == '__main__':

    db = conn_mongo.hotelgenome

    logger.info("[X] Loading categories")
    read_categories('out/loc_categories.csv')

    logger.info("[X] Fetching all location records")
    #hotels = db.hotel_pois_nokia.find(
    #        {"hotelId": {"$in": [228014,125813,188071,111189,212448]}}
    #        )
    hotels = db.hotel_pois_nokia.find()

    logger.info("[X] Starting saving location categories")
    for h in hotels:
        logger.debug("[.] Hotel Id %s" % h["hotelId"])
        places = [(r.get('category', {}).get('title', ""), r.get(
            'distance', None)) for r in h['places']]
        for dist_limit in DIST_BUCKETS:
            recs = collect_category_data(
                    h['hotelId'],
                    dist_limit,
                    places)
            save_loc_cat(recs)

