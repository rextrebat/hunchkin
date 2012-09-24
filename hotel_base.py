#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Copy Hotel Basic Data from Mongo"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import pymongo
import MySQLdb


conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
        )

conn_mongo = pymongo.Connection()

cursor = conn.cursor()

db = conn_mongo.hotelgenome

res = db.hotels.find()
names = [(r["hotelId"], r["name"]) for r in res]
cursor.executemany(
        """
        INSERT INTO hotel_basic
        (hotel_id, name)
        VALUES
        (%s, %s)
        """, names)
conn.commit()
conn.close()
