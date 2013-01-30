#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute overall distance based on chromosome distance"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import logging
#from celery import Celery
from celery.signals import worker_init, task_prerun
from itertools import groupby
import scipy
from operator import itemgetter
import ConfigParser

from bin.celeryapp import celery
from config.celeryconfig import env_config
#from config.celeryconfig import CeleryConfig


# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

hotels = None

unused_measure_types = ('unused', 'filter')

#celery = Celery('genome.chromosome_distance',
#       backend="amqp", broker="amqp://")
#celery.config_from_object(CeleryConfig)

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


def get_chromosome_similarity_better(hbase, hcomp):
    """
    parameters: chromosome lists for base and comp hotels
    Get how much "better" comp is w.r.t. base
    """
    return [v2 - v1 for (v1, v2) in zip(hbase, hcomp)]


def get_similarity(h1, h2, axes):
    """
    parameters: chromosomes of two hotels and axes
    axes: (category, sub_category, chromosome_name, chromosome_id)
    return: aggregate_similarity, similarity structure
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


def get_similarity_better(hbase, hcomp, axes):
    """
    parameters: chromosomes of two hotels and axes
    axes: (category, sub_category, chromosome_name, chromosome_id)
    return: aggregate_similarity, similarity structure
    """
    c_similarity = get_chromosome_similarity_better(hbase, hcomp)
    similarity = []
    for k1, g1 in groupby(axes, lambda x: x[0]):
        cat_sim = []
        for k2, g2 in groupby(g1, lambda x: x[1]):
            sub_cat_sim = []
            for g3 in g2:
                sub_cat_sim.append((g3[2], c_similarity[g3[3]]))
            sub_cat_sim.sort(key=itemgetter(1))
            cat_sim.append(
                    (
                        k2,
                        scipy.mean([float(s) for (c, s) in sub_cat_sim]),
                        sub_cat_sim
                        )
                    )
        cat_sim.sort(key=itemgetter(1))
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
def top_n_similar(base_h_id, comp_hotels, n_hotels=None, axes_omissions=[]):
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
        aggregate_similarity, similarity = get_similarity_better(
                base_hotel_chromosomes, comp_hotel_chromosomes[c], axes)
        similar_hotels.append((c, aggregate_similarity, similarity))
    similar_hotels.sort(key=itemgetter(1), reverse=True)
    if n_hotels:
        return similar_hotels[:n_hotels]
    else:
        return similar_hotels


def get_subcat_axes():
    """
    Get axes of all sub-categories with functions, bitmasks and names
    """
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, function, bitmask, gene_name
            FROM genome_rules
            ORDER by category, sub_category
            """
            )
    rows = cursor.fetchall()
    subcats = {}
    for k_cat, g_cat in groupby(rows, lambda r: r[0]):
        subcats[k_cat] = {}
        for k_subcat, g_subcat in groupby(g_cat, lambda r: r[1]):
            subcats[k_cat][k_subcat] = []
            for genes in g_subcat:
                subcats[k_cat][k_subcat].append(
                        (genes[2], genes[3], genes[4])
                        )
    return subcats


def get_hotel_genes_by_subcat(subcats, genome):
    """
    Get category, sub_category dict of gene values for a hotel
    """
    hotel_genes = {}
    for c, scs in subcats.iteritems():
        hotel_genes[c] = {}
        for sc, genes in scs.iteritems():
            hotel_genes[c][sc] = []
            for g in genes:
                if genome[g[1]] > 0:
                    if g[0] in ('exist', 'compare', 'value'):
                        hotel_genes[c][sc].append(g[2])
                    elif g[0] in ('loc_cat'):
                        hotel_genes[c][sc].append(
                                g[2] + "-" + str(int(round(genome[g[1]])))
                                )
    return hotel_genes


@celery.task
def get_gene_values(hotel_ids):
    """
    Get gene values for a list of hotels
    Return {'hotel_id': {'category': {'sub_category': genes...
    """
    hotel_genes = {}
    subcats = get_subcat_axes()
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT hotel_id, genome
            FROM hotel_genome
            WHERE hotel_id in (%s)
            """ % ",".join([str(h) for h in hotel_ids])
            )
    for hotel_id, genome_str in cursor.fetchall():
        genome = [float(g.strip()) for g in genome_str.split(",")]
        hotel_genes[hotel_id] = get_hotel_genes_by_subcat(
                subcats, genome)
    return subcats, hotel_genes


def connect_db():
    global conn
    config = ConfigParser.RawConfigParser()
    try:
        config.read('/etc/hunchkin.conf')
        env = config.get('environment', 'env')
        if env not in env_config:
            raise RuntimeError("Environment not defined")
        else:
            conf = env_config[env]
            conn = MySQLdb.Connection(
                    host=conf['db_host'],
                    user=conf['db_user'],
                    passwd=conf['db_passwd'],
                    db=conf['db_db']
                    )
    except:
        raise RuntimeError("Environment not defined")


@worker_init.connect
def initialize_genome_distance(sender=None, conf=None, **kwargs):

    logger.info("[1] Connecting to DB")
    connect_db()


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
        connect_db()
        logger.info("[X] Reconnected to DB")


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

    connect_db()

    #logger.info("[1] Loading Similarity Axes")
    #axes = get_axes()

    #logger.info("[2] Loading hotels data")
    #selection = [228014,125813,188071,111189,212448]

    logger.info("[1] Computing Distances")
    print top_n_similar(228014, [125813,188071,111189,212448], 3)

    logger.info("[2] Get Genes")
    subcats, hotel_genes = get_gene_values([125813, 188071])
    print hotel_genes

#    logger.info("[4] Timing 1000 invocations of genome distance function")
#    from timeit import timeit
#    print timeit('sim = top_n_similar(228014, [125813,188071,111189,212448], 3)',
#            setup='from __main__ import top_n_similar', number=1000)

    #logger.info("[4] Getting gene values")
    #print get_gene_values(228014, 125813, "HOTEL AMENITIES", "Pool")

    logger.info("[3] Done")
    conn.close()


