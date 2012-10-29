#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test for gene_crawler"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import unittest
# import mock
import genome_distance
import MySQLdb


class TestGenomeDistance(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        genome_distance.conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
        )
        genome_distance.get_axes()
        genome_distance.load_hotel(180345)
        genome_distance.load_hotel(337902)
        genome_distance.load_hotel(212154)
        genome_distance.load_hotel(361736)
        genome_distance.load_hotel(266042)
        genome_distance.load_hotel(267274)
        genome_distance.load_hotel(266433)
        genome_distance.load_hotel(356991)
        genome_distance.load_hotel(337596)
        genome_distance.load_hotel(338833)


    @classmethod
    def tearDownClass(cls):
        genome_distance.conn.commit()
        genome_distance.conn.close()


    def test_distances(self):
        genome_distance.hotel_similarities(180345)


if __name__ == '__main__':
    unittest.main()
