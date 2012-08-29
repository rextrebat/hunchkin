#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag genes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import pymongo
import MySQLdb
import nltk
import logging

# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

conn_mongo = None

GENOME_LENGTH = 1024


ign_words = set(['-', '(', ')', 's', '/', '.', ',',])
cmp_operators = ['==', '>', '<', '>=', '<=', '!=']

genome_rules = None

hotels = {}


def split_attr(attr_value):
    l = nltk.word_tokenize(attr_value.strip())
    l = [w for w in l if w not in ign_words]
    return set(l)


def compare(h_id, attr, comp):
    for c in cmp_operators:
        if c in comp:
            break
    t = comp.split(c)
    h_attr = hotels[h_id][attr]
    if type(h_attr) == dict:
        val = h_attr[t[0].strip()]
        exp = "val " + c + " " + t[1]
        return eval(exp)
    elif type(h_attr) == list:
        b = split_attr(t[0])
        val = None
        for a in h_attr:
            if b.issubset(a):
                for ai in a:
                    if ai.isdigit():
                        val = int(ai)
                if val:
                    exp = "val " + c + " " + t[1]
                    return eval(exp)
    return False


def match(h_id, attr, tag):
    h_attr = hotels[h_id][attr]
    if type(h_attr) != list:
        return False
    tags = tag.split("OR")
    for t in tags:
        b = split_attr(t)
        for a in h_attr:
            if b.issubset(a):
                return True
    return False


def load_genome_rules():
    global genome_rules
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT bitmask, gene_code, gene_rule 
            FROM genome_rules
            WHERE gene_rule != ""
            """
            )
    genome_rules = cursor.fetchall()
    cursor.close()


def hotel_attrs(h_id):
    global hotels
    db = conn_mongo.hotelgenome
    hotel_amenity = []
    room_amenity = []
    hotel_main = db.hotels.find_one({"hotelId": h_id})
    desc = db.hotel_descs.find_one({"@hotelId": str(h_id)})

    if "RoomTypes" in desc and "RoomType" in desc["RoomTypes"]:
        room_types = desc["RoomTypes"]["RoomType"]
        if type(room_types) != list:
            room_types = [room_types]
        for r in room_types:
            if "roomAmenities" in r and "RoomAmenity" in r["roomAmenities"]:
                amenities = r["roomAmenities"]["RoomAmenity"]
                if type(amenities) != list:
                    amenities = [amenities]
                for a in amenities:
                    room_amenity.append(split_attr(a["amenity"].strip()))

    if "PropertyAmenities" in desc and "PropertyAmenity" in desc[
            "PropertyAmenities"]:
        prop_amenities = desc["PropertyAmenities"]["PropertyAmenity"]
        if type(prop_amenities) != list:
            prop_amenities = [prop_amenities]
        for a in prop_amenities:
            hotel_amenity.append(split_attr(a["amenity"].strip()))

    hotels[h_id] = {
            "hotel_main": hotel_main,
            "hotel_amenity": hotel_amenity,
            "room_amenity": room_amenity,
            }


def gene_present(h_id, rule):
    t = rule.split("(")
    func = t[0] + "(" + str(h_id) + "," + ''.join(t[1:])
    return eval(func)


def tag_hotel(h_id):
    genome = [0] * GENOME_LENGTH
    cursor = conn.cursor()
    for rule in genome_rules:
        bitmask, gene_code, gene_rule = rule
        if gene_present(h_id, gene_rule):
            genome[bitmask] = 1
    genome_str = ''.join([str(g) for g in genome])
    logger.debug("genome for h_id %d: %s" % (h_id, genome_str))
    cursor.execute(
            """
            INSERT INTO hotel_genome
            (hotel_id, genome)
            VALUES
            (%s, %s)
            ON DUPLICATE KEY UPDATE
            genome = %s
            """,
            (h_id, genome_str, genome_str)
            )
    cursor.close()


def load_all_hotels():
    db = conn_mongo.hotelgenome
    res = db.hotels.find()
    for h in res:
        hotel_attrs(h["hotelId"])


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

    conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
    )
    conn_mongo = pymongo.Connection("localhost")

    logger.info("[1] Loading genome rules")
    load_genome_rules()

    logger.info("[2] Loading hotels data")
    load_all_hotels()

    logger.info("[3] Tagging hotel genes")
    for h in hotels.iterkeys():
        tag_hotel(h)

    logger.info("[4] Done tagging")
    conn.commit()
    conn.close()
