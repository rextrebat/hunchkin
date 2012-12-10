#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute overall distance based on chromosome distance"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import logging
from collections import namedtuple
from celery import Celery
from celery.signals import worker_init, task_prerun
from itertools import groupby
import scipy
from operator import itemgetter

from config.celeryconfig import CeleryConfig

# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

hotels = None

unused_measure_types = ('unused', 'filter')

celery = Celery('genome.chromosome_distance',
        backend="amqp", broker="amqp://")
celery.config_from_object(CeleryConfig)

CHROMOSOME_LENGTH = 150


def get_axes(omit=[]):
    axes = []
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, chromosome, chromosome_id,
            category_order, measure_type
            FROM genome_categories
            ORDER by category_order, category, sub_category, chromosome
            """
            )
    rows = cursor.fetchall()
    for r in rows:
        category, sub_category, chromosome_name, chromosome_id, \
                category_order, measure_type = r
        if measure_type not in unused_measure_types:
            if (category, sub_category, chromosome_name) not in omit:
                axes.append(
                        (category, sub_category, 
                            chromosome_name, chromosome_id))
    cursor.close()
    return axes


def get_hotel_chromosome_from_cache(h_id):
    return None


def put_hotel_chromosome_in_cache(h_id, chromosomes):
    return


def get_hotel_chromosomes(hotel_ids):
    """
    Create a list with chromosome_id offset as the score for that chromosome
    FIXME: Add cache functionality
    """
    if not hotel_ids:
        return None
    hotel_id_in = ','.join([str(h) for h in hotel_ids])
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT hotel_id, chromosome_id, normalized_score
            FROM hotel_chromosome
            WHERE hotel_id in (%s)
            ORDER BY hotel_id, chromosome_id
            """ % hotel_id_in
            )
    results = cursor.fetchall()
    hotel_chromosomes = {}
    for key, group in groupby(results, lambda x: x[0]):
        chromosomes = [0.0]*CHROMOSOME_LENGTH
        for g in group:
            chromosomes[g[1]] = g[2]
        hotel_chromosomes[key] = chromosomes
    cursor.close()
    return hotel_chromosomes


def get_chromosome_similarity(h1, h2):
    """
    parameters: two chromosome score lists
    Get 1 - (absolute distance) on each chromosome
    """
    return [1 - abs(v1 - v2) for (v1, v2) in zip(h1, h2)]


def get_similarity(h1, h2, axes):
    """
    parameters: chromosomes of two hotels and axes
    axes: (category, sub_category, chromosome_name, chromosome_id)
    return: aggregate_similarity, category_similarity, sub_category_similarity
    """
    c_similarity = get_chromosome_similarity(h1, h2)
    similarity = []
    for k1, g1 in groupby(axes, lambda x: x[0]):
        cat_sim = []
        for k2, g2 in groupby(g1, lambda x: x[1]):
            sub_cat_sim = []
            for g3 in g2:
                sub_cat_sim.append((g3[2], c_similarity[g3[3]]))
            sub_cat_sim.sort(key=itemgetter(1), reverse=True)
            cat_sim.append(
                    (
                        k2,
                        scipy.mean([float(s) for (c, s) in sub_cat_sim]),
                        sub_cat_sim
                        )
                    )
        cat_sim.sort(key=itemgetter(1), reverse=True)
        similarity.append(
                (
                    k1,
                    scipy.mean([s for (sc, s, c) in cat_sim]),
                    cat_sim
                    )
                )
    aggregate_similarity = scipy.mean(
            [s for (c, s, sc) in similarity]
            )
    return (aggregate_similarity, similarity)


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
    base_hotel_chromosomes = get_hotel_chromosomes([base_h_id])[base_h_id]
    comp_hotel_chromosomes = get_hotel_chromosomes(comp_hotels)
    for c in comp_hotels:
        aggregate_similarity, similarity = get_similarity(
                base_hotel_chromosomes, comp_hotel_chromosomes[c], axes)
        similar_hotels.append((c, aggregate_similarity, similarity))
    similar_hotels.sort(key=itemgetter(1), reverse=True)
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


    #logger.info("[1] Loading Similarity Axes")
    #axes = get_axes()

    #logger.info("[2] Loading hotels data")
    #selection = [228014,125813,188071,111189,212448]

    logger.info("[3] Computing Distances")
    print top_n_similar(228014, [125813,188071,111189,212448], 3)

#    logger.info("[4] Timing 1000 invocations of genome distance function")
#    from timeit import timeit
#    print timeit('sim = top_n_similar(228014, [125813,188071,111189,212448], 3)',
#            setup='from __main__ import top_n_similar', number=1000)

    #logger.info("[4] Getting gene values")
    #print get_gene_values(228014, 125813, "HOTEL AMENITIES", "Pool")

    logger.info("[5] Done")
    conn.close()


