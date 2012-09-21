#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test for gene_crawler"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

logger = logging.getLogger("loc_gd")

import unittest
# import mock
import genome_distance
import pymongo
import MySQLdb


class GenomeDistanceLocation(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        genome_distance.conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
        )
        genome_distance.get_axes()
        mongo = pymongo.Connection("localhost")
        db = mongo.hotelgenome
        h_query = db.locations.find_one({"loc": 5}, {"query": 1})
        h_query = h_query["query"]
        h_query = 'db.hotels.find(' + h_query + ')'
        res = eval(h_query)
        for h in res:
            genome_distance.load_hotel(h["hotelId"])
        mongo.close()


    @classmethod
    def tearDownClass(cls):
        genome_distance.conn.commit()
        genome_distance.conn.close()


    def test_distances(self):
        for h in genome_distance.hotels.iterkeys():
            logger.info("Distances for hotel %d", h)
            genome_distance.hotel_similarities(h)


if __name__ == '__main__':
    unittest.main()
