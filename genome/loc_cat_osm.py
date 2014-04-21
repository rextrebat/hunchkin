#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Location Categories - latest based on Open Street Maps Data"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
import MySQLdb

# ---GLOBALS
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger("loc_category")

# location categories based on OSM Poi_types
POI_TYPES = {
    'Essential Services': range(8, 18) + range(30, 36) + range(46, 48),
    'Dining': [25, 26, 27, 29],
    'Nightlife': [23, 24, 28],
    'Shopping': range(73, 110),
    'Sports': range(110, 137),
    'Tourist Attractions': range(137, 159),
    'Transportation': range(159, 169)
    }

DIST_BUCKETS = (1.0, 5.0)

conn = MySQLdb.Connection(
    host="localhost",
    user="appuser",
    passwd="rextrebat",
    db="hotel_genome"
)

conn_ean = MySQLdb.Connection(
    host = "localhost",
    user = "eanuser",
    passwd = "ean!BogolTola",
    db = "eanprod"
)

def get_loc_categories():
    """
    Returns distionary of categories with empty counts
    """
    return {
        'Essential Services': 0,
        'Dining': 0,
        'Nightlife': 0,
        'Shopping': 0,
        'Sports': 0,
        'Tourist Attractions': 0,
        'Transportation': 0,
        }

def which_category(poi_type):
    """
    Find which category poi belongs to
    """
    for k, v in POI_TYPES.iteritems():
        if poi_type in v:
            return k
    return "None"


def get_hotel_loc_categories(hotel_id, h_lat, h_long):
    """
    For a given hotel (identified by its lat and long),
    get the associate pois
    Return: list of (hotel_id, distance, category, count)
    """
    hotel_loc_categories = []
    cursor = conn.cursor()
    for dist in DIST_BUCKETS:
        lc = get_loc_categories()
        cursor.execute(
                """
                SELECT poi_type
                FROM (
                    SELECT poi_type, latitude, longitude, r,
                    111.045* DEGREES(ACOS(COS(RADIANS(latpoint))
                        * COS(RADIANS(latitude))
                        * COS(RADIANS(longpoint) - RADIANS(longitude))
                        + SIN(RADIANS(latpoint))
                        * SIN(RADIANS(latitude)))) AS distance_in_km
                    FROM osm_pois
                        JOIN (
                            SELECT %s AS latpoint, %s AS longpoint, %s AS r
                             ) AS p
                        WHERE latitude
                        BETWEEN latpoint  - (r / 111.045)
                        AND latpoint  + (r / 111.045)
                        AND longitude
                        BETWEEN longpoint - (r / (111.045 * COS(RADIANS(latpoint))))
                        AND longpoint + (r / (111.045 * COS(RADIANS(latpoint))))
                        ) d
                WHERE distance_in_km <= r
                """ % (str(h_lat), str(h_long), str(dist))
                )
        results = cursor.fetchall()
        for r in results:
            cat = which_category(r[0])
            if cat != "None":
                lc[cat] += 1
        for k, v in lc.iteritems():
            hotel_loc_categories.append(
                    (hotel_id, dist, k, v)
                    )
    return hotel_loc_categories


def save_hotel_loc_categories(recs):
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


    logger.info("[X] Fetching all location records")
    #hotels = [(404429, -54.81275, -68.34416)]
    cursor = conn_ean.cursor()
    cursor.execute(
            """
            SELECT EANHotelID, Latitude, Longitude
            FROM activepropertylist
            """
            )
    hotels = cursor.fetchall()

    logger.info("[X] Starting saving location categories")
    for i, h in enumerate(hotels):
        logger.debug("[%s] Hotel Id %s" % (i, h[0]))
        hotel_loc_categories = get_hotel_loc_categories(
                h[0], h[1], h[2]
                )
        #print hotel_loc_categories
        save_hotel_loc_categories(hotel_loc_categories)

