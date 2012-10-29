#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag genes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import logging
from timeit import timeit

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
            SELECT c.category, c.sub_category, 
            c.measure_type, c.similarity_function, 
            GROUP_CONCAT(r.bitmask SEPARATOR ',')
            FROM genome_categories c, genome_rules r
            WHERE c.sub_category = r.sub_category
            AND c.category = r.category
            GROUP by c.category, c.sub_category;
            """
            )
    rows = cursor.fetchall()
    for r in rows:
        category, sub_category, measure_type, similarity_function,\
                bits = r
        axes[category + "|" + sub_category] = dict(
                measure_type=measure_type,
                similarity_function=similarity_function,
                bits=eval("[" + bits + "]")
                )
    cursor.close()


def modified_simple_match(g1, g2):
    """
    Parameters - lists with gene values
    Modified simple matching - (m00 + m11) / (m00 + m01 + m10 + m11)
    m00 (absent in both) is down-weighted by 50%
    """
    g = zip(g1, g2)
    m11 = float(len([p for p in g if p[0] == 1 and p[1] == 1]))
    m00 = float(len([p for p in g if p[0] == 0 and p[1] == 0]))
    m01 = float(len([p for p in g if p[0] == 0 and p[1] == 1]))
    m10 = float(len([p for p in g if p[0] == 1 and p[1] == 0]))
    den = m11 + 0.5*m00 + m01 + m10
    if den:
        return (m11 + 0.5*m00) / den
    else:
        return 0


def jaccard_similarity(g1, g2):
    """
    Parameters - lists with gene VALUES
    Return - jaccard distance (float)
    http://en.wikipedia.org/wiki/Jaccard_index
    """
    g = zip(g1, g2)
    m11 = float(len([p for p in g if p[0] == 1 and p[1] == 1]))
    m01 = float(len([p for p in g if p[0] == 0 and p[1] == 1]))
    m10 = float(len([p for p in g if p[0] == 1 and p[1] == 0]))
    # m00 = float(len([p for p in g if p[0] == 0 and p[1] == 0]))
    if m11:
        return m11 / (m01 + m10 + m11)
    else:
        return 0


def cosine_similarity(g1, g2):
    """
    Parameters - lists with gene values
    """
    g = zip(g1, g2)
    dotp = float(sum([p[0] * p[1] for p in g]))
    modg1 = float(sum(p ** 2 for p in g1)) ** 0.5
    modg2 = float(sum(p ** 2 for p in g2)) ** 0.5
    den = modg1 * modg2
    if den:
        return dotp / den
    else:
        return 0


def hotel_similarity_vector(h1, h2):
    """
    Parameters: hotel ids
    Output: dict of distance(float) by axis
    """
    similarity = {}
    for a, v in axes.iteritems():
        g1 = [hotels[h1][b] for b in v['bits']]
        g2 = [hotels[h2][b] for b in v['bits']]
        if v['measure_type'] != 'Unused':
            if v['similarity_function'] == 'Cosine':
                similarity[a] = cosine_similarity(g1, g2)
            elif v['similarity_function'] == 'Modified_Simple_Match':
                similarity[a] = modified_simple_match(g1, g2)
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


def load_hotels(selection=None):
    """
    Load all hotels in DB otherwise only selection
    """
    cursor = conn.cursor()
    query = """
    SELECT hotel_id, genome
    FROM hotel_genome
    """
    if selection:
        selection = [str(s) for s in selection]
        query += """
        WHERE hotel_id in (%s)
        """ % ",".join(selection)
    cursor.execute(query)
    rows = cursor.fetchall()
    for r in rows:
        hotels[r[0]] = eval("[" + r[1] + "]")


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
    selection = [228014,125813,188071,111189,212448]
    load_hotels(selection)

    logger.info("[3] Computing Distances")
    print hotel_similarity_vector(228014, 125813)

    logger.info("[4] Timing 1000 invocations of genome distance function")
    print timeit('sim = hotel_similarity_vector(228014, 125813)',
            setup='from __main__ import hotel_similarity_vector', number=1000)

    logger.info("[5] Done")
    conn.close()
