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


def compare(comp, attr, value):
    if comp == "gt":
        return attr > value
    if comp == "ge":
        return attr >= value
    if comp == "eq":
        return attr == value
    if comp == "le":
        return attr <= value
    if comp == "lt":
        return attr < value


def exist(attr_dict, attrs):
    for a in attrs:
        if a in attr_dict:
            return True
    return False


def value(attr_dict, attr):
    return attr_dict.get(attr, None)


genome_rules = None

hotels = {}


def load_genome_rules():
    global genome_rules
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT bitmask, gene_code, gene_source, function, parameters 
            FROM genome_rules
            WHERE function != ""
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
