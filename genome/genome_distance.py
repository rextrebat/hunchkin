#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag genes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import logging
from timeit import timeit
from collections import namedtuple
from celery import Celery
import celery
from celery.signals import worker_init, task_prerun

# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

hotels = None

celery = Celery('genome_distance', backend="amqp", broker="amqp://")


SimilarHotel = namedtuple(
        'SimilarHotel',
        'hotel_id, similarity, aggregate_similarity'
        )


def get_axes(omit=[]):
    axes = {}
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT c.category, c.sub_category,
            c.measure_type, c.similarity_function, c.category_order,
            c.normalization_factor,
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
                category_order, normalization_factor, bits = r
        if measure_type != "Unused":
            key = category + "|" + sub_category
            if key not in omit:
                axes[key] = dict(
                        measure_type=measure_type,
                        similarity_function=similarity_function,
                        category_order=category_order,
                        bits=eval("[" + bits + "]"),
                        normalization_factor=normalization_factor
                        )
    cursor.close()
    return axes


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


def euclidean_similarity(g1, g2, normalization_factor):
    """
    Simple euclidean distance
    """
    g = zip(g1, g2)
    dist = float(sum([(p[0] -p[1]) ** 2 for p in g])) ** 0.5
    norm_dist = dist / normalization_factor
    return (1.0 - norm_dist)


def loc_step(v):
    """
    Step function for location data
    //FIXME: do better statistical analysis
    """
    if v < 3:
        return 1
    if v < 6:
        return 2
    if v < 10:
        return 3
    if v < 15:
        return 4
    if v < 25:
        return 5
    else:
        return 6


def loc_euclidean_similarity(g1, g2, normalization_factor):
    """
    Step-function on measure + Euclidean distance
    //FIXME: Needs to be fixed in raw data
    only scalar values here
    """
    g1 = [loc_step(v) for v in g1]
    g2 = [loc_step(v) for v in g2]
    return euclidean_similarity(g1, g2, normalization_factor)


@celery.task
def hotel_similarity_vector(axes, h1, h2):
    """
    Parameters: hotel ids
    Output: dict of distance(float) by axis
    """
    logger.debug("Similarity: %d %d" % (h1, h2))
    similarity = {}
    for a, v in axes.iteritems():
        g1 = [hotels[h1][b] for b in v['bits']]
        g2 = [hotels[h2][b] for b in v['bits']]
        if v['similarity_function'] == 'Cosine':
            similarity[a] = round(cosine_similarity(g1, g2),2)
        elif v['similarity_function'] == 'Modified_Simple_Match':
            similarity[a] = round(modified_simple_match(g1, g2),2)
        elif v['similarity_function'] == 'Euclidean':
            similarity[a] = round(euclidean_similarity(
                g1, g2, v['normalization_factor']),2)
        elif v['similarity_function'] == 'Loc_Euclidean':
            similarity[a] = round(loc_euclidean_similarity(
                g1, g2, v['normalization_factor']),2)
    return similarity


def aggregate_similarity(similarity):
    """
    Return the aggregate similarity
    """
    return sum([v for v in similarity.itervalues()])


@celery.task
def top_n_similar(base_h_id, comp_hotels, n_hotels, axes_omissions=[]):
    """
    Find the top n similar hotels
    base_h_id: base hotel to compare to
    comp_hotels: list of hotels to compare with
    n_hotels: number of hotels to return
    return: list with (hotel_id, similarity, aggregate_similarity) tuples 
    in sorted order
    """
    axes = get_axes(axes_omissions)
    similar_hotels = []
    for c in comp_hotels:
        similarity = hotel_similarity_vector(axes, base_h_id, c)
        aggregate_similarity = sum([v for v in similarity.itervalues()])
        similar_hotels.append(SimilarHotel(
                c, similarity, aggregate_similarity))
    similar_hotels.sort(key=lambda sim: sim[2], reverse=True)
    return similar_hotels[:n_hotels]


@celery.task
def get_gene_values(base_h_id, comp_h_id, category, sub_category):
    """
    Get actual gene values for a sub_category
    Return (gene_name, base_value, comp_value)
    """
    axes = get_axes()
    bits = axes[category + "|" + sub_category]["bits"]
    bits = [str(bit) for bit in bits]
    cursor = conn.cursor()
    print bits
    cursor.execute(
            """
            SELECT DISTINCT gene_name, bitmask
            FROM genome_rules
            WHERE bitmask IN (%s)
            """ % ','.join(bits)
            )
    rows = cursor.fetchall()
    gene_values = []
    for r in rows:
        name, bit = r
        gene_values.append((
            name,
            hotels[base_h_id][bit],
            hotels[comp_h_id][bit]
            ))
    cursor.close()
    return gene_values


def load_hotels(selection=None):
    """
    Load all hotels in DB otherwise only selection
    """
    global hotels
    hotels = {}
    logging.debug("[X] Starting loading hotels...")
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
    logging.debug("[X] Done loading hotels...")
    cursor.close()


@worker_init.connect
def initialize_genome_distance(sender=None, conf=None, **kwargs):

    global conn
    logger.info("[1] Connecting to DB")
    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )

    logger.info("[2] Loading hotels data")
    load_hotels()


@task_prerun.connect
def check_connection(**kwargs):

    global conn
    try:
        cursor = conn.cursor()
        cursor.execute(
                """
                SELECT category
                FROM hotel_genome
                LIMIT 1;
                """
                )
    except:
        conn.close()
        conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
        )
        logger.info("[X] Reconnected to DB")


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )


    logger.info("[1] Loading Similarity Axes")
    axes = get_axes()

    logger.info("[2] Loading hotels data")
    selection = [228014,125813,188071,111189,212448]
    load_hotels(selection)

    logger.info("[3] Computing Distances")
    print hotel_similarity_vector(axes, 228014, 125813)

    #logger.info("[4] Timing 1000 invocations of genome distance function")
    #print timeit('sim = hotel_similarity_vector(228014, 125813)',
    #        setup='from __main__ import hotel_similarity_vector', number=1000)

    logger.info("[4] Getting gene values")
    print get_gene_values(228014, 125813, "HOTEL AMENITIES", "Pool")

    logger.info("[5] Done")
    conn.close()


