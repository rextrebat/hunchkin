#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test for gene_crawler"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import unittest
# import mock
import gene_tagger
import MySQLdb
import pymongo


class TestGeneTagger(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        gene_tagger.conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
        )
        gene_tagger.conn_mongo = pymongo.Connection("localhost")
        gene_tagger.load_genome_rules()
        gene_tagger.hotel_attrs(224426)
        gene_tagger.hotel_attrs(415853)
        gene_tagger.hotel_attrs(141874)

    @classmethod
    def tearDownClass(cls):
        gene_tagger.conn.commit()
        gene_tagger.conn.close()


    def test_compare(self):
        self.assertTrue(gene_tagger.gene_present(
            224426,
            'compare("hotel_main", "hotelRating == 2.5")'
            ))
        self.assertFalse(gene_tagger.gene_present(
            415853,
            'compare("hotel_main", "hotelRating == 2.5")'
            ))
        self.assertFalse(gene_tagger.gene_present(
            224426,
            'compare("hotel_amenity", "Number of floors > 10")'
            ))
        self.assertTrue(gene_tagger.gene_present(
            224426,
            'compare("hotel_amenity", "Number of buildings/towers > 1")'
            ))

    def test_match(self):
        self.assertTrue(gene_tagger.gene_present(
            224426,
            'match("hotel_amenity", "Laundry facilities")',
            ))
        self.assertTrue(gene_tagger.gene_present(
            224426,
            'match("hotel_amenity", "Shopping on site OR Gift shops or newsstand OR Grocery/convenience store OR Grocery")',
            ))
        self.assertFalse(gene_tagger.gene_present(
            224426,
            'match("hotel_amenity", "Elevator/lift")',
            ))

    def test_genome(self):
        pass
        gene_tagger.tag_hotel(224426)
        gene_tagger.tag_hotel(415853)
        gene_tagger.tag_hotel(141874)


if __name__ == '__main__':
    unittest.main()
