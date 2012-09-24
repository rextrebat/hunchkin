#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Driver for location categories"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

logger = logging.getLogger("loc_sim")

import unittest
# import mock
import loc_category
import pymongo
import MySQLdb


class GenomeDistanceLocation(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        loc_category.conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
        )
        loc_category.conn_mongo = pymongo.Connection("localhost")
        loc_category.read_categories("out/loc_categories.csv")
        loc_category.category_order = [
                "Airport",
                "Banking",
                "Entertainment",
                "Medical",
                "Food",
                "Public Transport",
                "Shopping",
                "Tourist",
                "Other",
                ]


    @classmethod
    def tearDownClass(cls):
        loc_category.conn.commit()
        loc_category.conn.close()


    def test_loc_cat(self):
        db = loc_category.conn_mongo.hotelgenome
        hotels = db.hotels.find({}, {"hotelId":1})
        for h in hotels:
            h_id = h["hotelId"]
            logger.info("Location Categories for hotel %d", h_id)
            loc_category.save_loc_cat(
                    h_id,
                    loc_category.categorize_pois(
                        h_id))


if __name__ == '__main__':
    unittest.main()
