#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Location Scales"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
import MySQLdb
import scipy

# ---GLOBALS
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger("loc_category")

conn = MySQLdb.Connection(
    host="localhost",
    user="appuser",
    passwd="rextrebat",
    db="hotel_genome"
)

scale_percentiles = (20, 40, 60, 80, 100)

def get_all_genes():
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT genome
            FROM hotel_genome
            """
            )
    results = cursor.fetchall()
    cursor.close()
    return [map(float, r[0].split(",")) for r in results]


def get_scale(genes, bitmask):
    values = [g[bitmask] for g in genes]
    scale = [
            scipy.percentile(values, s) for s in scale_percentiles
            ]
    return tuple(scale)


def get_location_genes():
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, chromosome, bitmask
            FROM genome_rules
            WHERE category = "LOCATION"
            AND gene_usage = "Standard"
            """
            )
    results = cursor.fetchall()
    cursor.close()
    return results


def save_loc_scale(key, scale):
    cursor = conn.cursor()
    cursor.execute(
            """
            INSERT INTO loc_scales
            (category, sub_category, chromosome, p20, p40, p60, p80, p100)
            VALUES
            ('%s', '%s', '%s', %d, %d, %d, %d, %d)
            """ % tuple(key + scale)
            )
    conn.commit()
    cursor.close()


if __name__ == '__main__':


    logger.info("[X] Loading genes")
    genes = get_all_genes()

    logger.info("[X] Getting location genes")
    loc_genes = get_location_genes()

    logger.info("[X] Getting scales")
    for g in loc_genes:
        save_loc_scale((g[0], g[1], g[2]),
                get_scale(genes, g[3]))


