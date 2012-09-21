#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Driver for similar_hotels"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

logger = logging.getLogger("loc_sim")

import unittest
# import mock
import similar_hotels
import pymongo
import MySQLdb


class GenomeDistanceLocation(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        similar_hotels.conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
        )
        mongo = pymongo.Connection("localhost")
        db = mongo.hotelgenome
        h_query = db.locations.find_one({"loc": 5}, {"query": 1})
        h_query = h_query["query"]
        h_query = 'db.hotels.find(' + h_query + ')'
        res = eval(h_query)
        for h in res:
            similar_hotels.hotels.append(h["hotelId"])
        mongo.close()


    @classmethod
    def tearDownClass(cls):
        similar_hotels.conn.commit()
        similar_hotels.conn.close()


    def test_distances(self):
        for h in similar_hotels.hotels:
            logger.info("Similar Hotels for hotel %d", h)
            similar_hotels.top_similar(h)


if __name__ == '__main__':
    unittest.main()
