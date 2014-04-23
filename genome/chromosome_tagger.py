#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag chromosomes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import MySQLdb
from collections import namedtuple
from itertools import groupby
# ---GLOBALS

logger = logging.getLogger("chromosome_tagger")

conn = None

Chromosomes = []

hotels = []

LocScales = {}

Categories = {}

ChromosomeIds = {}

Chromosome = namedtuple(
        'Chromosome',
        'category, sub_category, chromosome_name, genes, total_weight'
        )

Hotel = namedtuple(
        'Hotel',
        'hotel_id, genome'
        )


def get_chromosomes():
    global Chromosomes
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, chromosome, bitmask, weight
            FROM genome_rules
            WHERE gene_usage = "Standard"
            ORDER BY category, sub_category, chromosome
            """
            )
    results = cursor.fetchall()
    for key, group in groupby(results, lambda x: x[:3]):
        genes = [(g[3], g[4]) for g in group]
        total_weight = sum([w for b,w in genes])
        Chromosomes.append(Chromosome(*(key + (genes, total_weight))))
    cursor.close()


def get_categories():
    global Categories
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, chromosome,
            normalization_method, normalization_factor
            FROM genome_categories
            """
            )
    for r in cursor.fetchall():
        Categories[(r[0], r[1], r[2])] = (r[3], r[4])
    cursor.close()


def get_chromosome_ids():
    global ChromosomeIds
    cursor = conn.cursor()
    cursor.execute(
            """
            select category, sub_category, chromosome, chromosome_id
            FROM genome_categories
            """
            )
    for r in cursor.fetchall():
        ChromosomeIds[(r[0], r[1], r[2])] = r[3]


def get_loc_scales():
    global LocScales
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, chromosome,
            p20, p40, p60, p80, p100
            FROM loc_scales
            """
            )
    for r in cursor.fetchall():
        LocScales[(r[0], r[1], r[2])] = (r[3], r[4], r[5], r[6], r[7])
    cursor.close()


def loc_scale_normalize(chromosome, score):
    scale = LocScales[
            (chromosome.category,
                chromosome.sub_category, chromosome.chromosome_name)]
    for i, v in enumerate(reversed(scale)):
        if score >= v:
            return float(i+1)/5
    return 0


def get_normalized_score(chromosome, genes):
    norm = Categories[
            (chromosome.category,
                chromosome.sub_category, chromosome.chromosome_name)]
    normalization_method, normalization_factor = norm
    score = sum([g for g,w in genes])
    normalized_score = score
    if normalization_method == "Maximum":
        normalized_score = score / normalization_factor
    elif normalization_method == "Weighted Mean":
        normalized_score = sum([g*w for g,w in genes]) / \
                chromosome.total_weight
    elif normalization_method == "Location Scaled":
        normalized_score = loc_scale_normalize(chromosome, score)
    return (score, normalized_score)


def get_chromosome_score(h):
    """
    Tag the chromosome for a given hotel
    """
    scores = []
    for chromosome in Chromosomes:
        genes = [
            (float(h.genome[b]), w) for b, w in chromosome.genes]
        score, normalized_score = get_normalized_score(chromosome, genes)
        normalized_score = round(normalized_score, 2)
        chromosome_id = ChromosomeIds[
                (chromosome.category,
                    chromosome.sub_category, chromosome.chromosome_name)]
        hcs = (
                h.hotel_id,
                chromosome_id,
                score,
                normalized_score
                )
        scores.append(hcs)
    return scores


def save_hotel_chromosome_score(h):
    """
    Calculate and save chromosomes for all hotels
    """
    cursor = conn.cursor()
    scores = get_chromosome_score(h)
    cursor.executemany(
            """
            INSERT INTO new_hotel_chromosome
            (hotel_id, chromosome_id,
            raw_score, normalized_score)
            VALUES
            (%s, %s, %s, %s)
            """, scores)
    conn.commit()
    cursor.close()


def load_hotels(selection=None):
    """
    Load all hotels in DB otherwise only selection
    """
    global hotels
    cursor = conn.cursor()
    query = """
    SELECT hotel_id, genome
    FROM new_hotel_genome
    """
    if selection:
        selection = [str(s) for s in selection]
        query += """
        WHERE hotel_id in (%s)
        """ % ",".join(selection)
    cursor.execute(query)
    rows = cursor.fetchall()
    hotels = [Hotel(
        r[0],
        r[1].split(",")
        ) for r in rows]
    logger.debug("Loaded %d hotels" % len(hotels))
    cursor.close()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )


    logger.info(
            "[1] Loading chromosomes, categories, chromosome_ids and loc_scales")
    get_chromosomes()
    get_categories()
    get_chromosome_ids()
    get_loc_scales()

    logger.info("[2] Loading hotels data")
    selection = [228014,125813,188071,111189,212448]
    #load_hotels(selection)
    load_hotels()

    logger.info("[3] Tagging hotel chromosomes")
    for i, h in enumerate(hotels):
        save_hotel_chromosome_score(h)
        logger.debug("[%s] Hotel Id: %d" % (i, h.hotel_id))

    logger.info("[4] Done tagging")
    conn.commit()
    conn.close()
