#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LSA Dining"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import logging
import lsa

# ---GLOBALS

logger = logging.getLogger("lsa_dining")

conn = None

hotels = []


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )


    logger.info("[1] Loading hotels data")
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT EANHotelID, DiningDescription
            FROM EAN_DiningDescriptions d, loc_hotels l
            WHERE l.hotel_id = d.EANHotelID
            AND l.location_id = 5
            """
            )
    res = cursor.fetchall()
    h_count = 0
    for r in res:
        h_id, dining_desc = r
        hotels.append(
                dict(count=h_count, h_id=h_id, dining_desc=dining_desc))


    logger.info("[2] LSA")
    mylsa = lsa.LSA()
    for h in hotels:
        mylsa.parse(h["dining_desc"])
    mylsa.build()
    mylsa.histogram()
    print mylsa.hist[:100]
    mylsa.printA()
    mylsa.calc()
    mylsa.printSVD()

    logger.info("[3] Done")
    conn.commit()
    conn.close()
