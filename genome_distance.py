#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag genes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import logging

# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

hotels = {}

axes = {}


def get_axes():
    global axes
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT sub_category, GROUP_CONCAT(bitmask SEPARATOR ',')
            FROM genome_rules GROUP BY sub_category
            """
            )
    res = cursor.fetchall()
    for r in res:
        if r[1]:
            l = eval("[" + r[1] + "]")
        else:
            l = []
        axes[r[0]] = l
    cursor.close()


def jaccard_similarity(g1, g2):
    """
    Parameters - lists with gene VALUES
    Return - jaccard distance (float)
    http://en.wikipedia.org/wiki/Jaccard_index
    """
    g = zip(g1, g2)
    m11 = float(len([p for p in g if p[0] == "1" and p[1] == "1"]))
    m01 = float(len([p for p in g if p[0] == "0" and p[1] == "1"]))
    m10 = float(len([p for p in g if p[0] == "1" and p[1] == "0"]))
    # m00 = float(len([p for p in g if p[0] == "0" and p[1] == "0"]))
    if m11:
        return m11 / (m01 + m10 + m11)
    else:
        return 0


def hotel_similarity_vector(h1, h2):
    """
    Parameters: hotel ids
    Output: dict of distance(float) by axis
    """
    similarity = {}
    for a, l in axes.iteritems():
        g1 = [hotels[h1][b] for b in l]
        g2 = [hotels[h2][b] for b in l]
        similarity[a] = jaccard_similarity(g1, g2)
    return similarity


def hotel_similarities(h_id):
    """
    Parameters: hotel id
    Saves similarity into db for all others in the hotels dict
    """
    cursor = conn.cursor()
    for h in hotels.iterkeys():
        if h <= h_id:
# hotel_a is always the smaller id. This check ensures that two hotels are
# compared only once
            continue
        cursor.execute(
                """
                DELETE FROM hotel_similarity
                WHERE hotel_a = %s AND hotel_b = %s
                """, (h_id, h))
        sim = hotel_similarity_vector(h_id, h)
        sim_recs = []
        logger.debug(sim)
        for a, v in sim.iteritems():
            sim_recs.append((
                        h_id, h, a, round(v, 2)))
        if sim_recs:
            cursor.executemany(
                    """
                    INSERT INTO hotel_similarity
                    (hotel_a, hotel_b, sim_axis, sim_value)
                    VALUES
                    (%s, %s, %s, %s)
                    """, sim_recs)
    conn.commit()
    cursor.close()


def load_hotel(h_id=None):
    """
    Parameter: h_id; None implies load all hotels
    Load hotels into dict
    """
    cursor = conn.cursor()
    if h_id:
        cursor.execute(
                """
                SELECT hotel_id, genome FROM hotel_genome
                WHERE hotel_id = %s
                """, h_id)
    else:
        cursor.execute(
                """
                SELECT hotel_id, genome FROM hotel_genome
                """
                )
    for r in cursor.fetchall():
        hotels[r[0]] = r[1]
    cursor.close()


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )


    logger.info("[1] Loading Similarity Axes")
    get_axes()

    logger.info("[2] Loading hotels data")
    load_hotel()

    logger.info("[3] Computing Distances")
    for h in hotels.iterkeys():
        logger.info("Distances for hotel %d", h)
        hotel_similarities(h)

    logger.info("[4] Done")
    conn.commit()
    conn.close()
