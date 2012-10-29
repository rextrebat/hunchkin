#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag genes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import MySQLdb
from collections import namedtuple
import abc
import itertools
# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

conn_mongo = None

GENOME_LENGTH = 512

GeneRule = namedtuple(
        'GeneRule',
        'gene_code bitmask hotel_field function param'
        )

LocCat = namedtuple(
        'LocCat',
        'category, distance, count'
        )

HotelGenome = []

hotels = []

class GeneFunctionBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_gene_value(self, field, gene):
        return


class GF_Compare(GeneFunctionBase):

    comp_funcs = {
            'gt': lambda a,b: (a > b),
            'ge': lambda a,b: (a >= b),
            'eq': lambda a,b: (a == b),
            'le': lambda a,b: (a <= b),
            'lt': lambda a,b: (a < b),
            }

    def get_gene_value(self, field, gene_rule):
        comp, attrs, value = gene_rule.param.split("|")
        comp = comp.strip()
        value = value.strip()
        attrs = attrs.strip().split(",")
        for attr in attrs:
            if attr in field:
                attr_value = field[attr]
                if self.comp_funcs[comp](attr_value, value):
                    return 1
        return 0


class GF_Exist(GeneFunctionBase):

    def get_gene_value(self, field, gene_rule):
        attrs = gene_rule.param.split(",")
        for a in attrs:
            if int(a.strip()) in field:
                return 1
        return 0


class GF_LocCat(GeneFunctionBase):

    def get_gene_value(self, field, gene_rule):
        cat, dist = gene_rule.param.split(",")
        for lc in field:
            if cat.strip() == lc.category and int(dist) == lc.distance:
                return lc.count
        return 0


class GF_Value(GeneFunctionBase):

    def get_gene_value(self, field, gene_rule):
        return field.get(gene_rule.param.strip(), 0)


class Hotel(object):

    gene_func = {
            'compare': GF_Compare(),
            'exist': GF_Exist(),
            'loc_cat': GF_LocCat(),
            'value': GF_Value(),
            }

    def __init__(
            self,
            hotel_id,
# hotel_basic is a dict
            hotel_basic=None,
# hotel_amenities is a dict
            hotel_amenities=None,
# hotel_loc_cat is a list of LocCat tuples
            hotel_loc_cat=None
            ):
        self.hotel_id = hotel_id
        self.hotel_basic = hotel_basic
        self.hotel_amenities = hotel_amenities
        self.hotel_loc_cat = hotel_loc_cat

    def get_field(self, field_name):
        if field_name == 'basic':
            return self.hotel_basic
        if field_name == 'amenity':
            return self.hotel_amenities
        if field_name == 'location':
            return self.hotel_loc_cat

    def get_gene_value(self, gene_rule):
        field = self.get_field(gene_rule.hotel_field)
        if not gene_rule.function:
            return 0
        else:
            return self.gene_func[gene_rule.function].get_gene_value(
                    field, gene_rule)

    def get_genome(self, gene_rules):
        genome = [0]*GENOME_LENGTH
        for gene_rule in gene_rules:
            genome[gene_rule.bitmask] = self.get_gene_value(
                    gene_rule)
        return genome


def load_genome_rules():
    global HotelGenome
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT gene_code, bitmask, gene_source, function, parameters 
            FROM genome_rules
            WHERE function != ""
            """
            )
    genome_rules = cursor.fetchall()
    for gr in genome_rules:
        HotelGenome.append(GeneRule(gr[0], gr[1], gr[2], gr[3], gr[4]))
    cursor.close()


def load_hotels(selection=None):
    """
    Load all hotels in DB otherwise only selection
    """
    cursor = conn.cursor()
    query = """
    SELECT EANHotelID, StarRating
    FROM EAN_ActiveProperties
    """
    if selection:
        selection = [str(s) for s in selection]
        query += """
        WHERE EANHotelID in (%s)
        """ % ",".join(selection)
    cursor.execute(query)
    rows = cursor.fetchall()
    for r in rows:
        hotel_id = r[0]
        basic = dict(itertools.izip(
            ["EANHotelID", "StarRating"],r))
        cursor.execute(
                """
                SELECT AttributeID, AppendTxt
                FROM EAN_PropertyAttributeLink
                WHERE EANHotelID = %s
                """ % (hotel_id)
                )
        am_rows = cursor.fetchall()
        amenities = dict(am_rows)
        cursor.execute(
                """
                SELECT category, distance, count
                FROM loc_categories
                WHERE hotel_id = %s
                """ % (hotel_id)
                )
        lc_rows = cursor.fetchall()
        loc_cat = [LocCat(lc[0], lc[1], lc[2]) for lc in lc_rows]
        hotels.append(
                Hotel(
                    hotel_id=hotel_id,
                    hotel_basic=basic,
                    hotel_amenities=amenities,
                    hotel_loc_cat=loc_cat
                    )
                )


def save_hotel_genome(h, gene_rules):
    """
    Save the genome for the hotel
    """
    cursor = conn.cursor()
    genome = h.get_genome(gene_rules)
    genome = [str(g) for g in genome]
    genome = ','.join(genome)
    logger.debug("genome for h_id %s: %s" % (
        h.hotel_id, genome))
    query = """
            INSERT INTO hotel_genome
            (hotel_id, genome)
            VALUES
            (%s, '%s')
            ON DUPLICATE KEY UPDATE
            genome = '%s'
            """ % (h.hotel_id, genome, genome)
    cursor.execute(query)
    cursor.close()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )

    logger.info("[1] Loading genome rules")
    load_genome_rules()

    logger.info("[2] Loading hotels data")
    # selection = [228014,125813,188071,111189,212448]
    load_hotels()

    logger.info("[3] Tagging hotel genes")
    for h in hotels:
        save_hotel_genome(h, HotelGenome)

    logger.info("[4] Done tagging")
    conn.commit()
    conn.close()
