#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Save top similar hotels for a given hotel"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging

# ---GLOBALS

logger = logging.getLogger("similar_hotels")

conn = None

TOP_N = 10

hotels = []

def top_similar(h_id):
    """
    Save the top n similar hotels - similarity score is sum across dimensions
    """
    cursor = conn.cursor()
    cursor.execute(
            """
            INSERT INTO top_similar_hotels
            (hotel_a, hotel_b, sim_score)
            SELECT %s, hotel_id, sim_score
            FROM
            (SELECT hotel_b AS hotel_id, sum(sim_value) AS sim_score
            FROM hotel_similarity 
            WHERE hotel_a = %s
            GROUP BY hotel_b
            UNION
            SELECT hotel_a AS hotel_id, sum(sim_value) AS sim_score
            FROM hotel_similarity
            WHERE hotel_b = %s
            GROUP BY hotel_a) scores
            ORDER BY sim_score DESC LIMIT %s
            """, (h_id, h_id, h_id, TOP_N)
            )
    conn.commit()
