#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Store Genome Rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import csv
import MySQLdb


conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
        )

cursor = conn.cursor()

count = 0

with open("out/genome_categories.csv") as f:
    cursor.execute(
            """
            DELETE FROM genome_categories
            """
            )
    for r in csv.DictReader(f):
        for k, v in r.iteritems():
            r[k] = v.strip()
        category = r['Category']
        sub_category = r['Sub-category']
        measure_type = r['Type']
        similarity_function = r['Similarity_function']
        category_order = r['Order']
        cursor.execute(
                """
                INSERT INTO genome_categories 
                (
                category, sub_category, measure_type,
                similarity_function, category_order
                )
                VALUES
                (%s, %s, %s, %s, %s)
                """,
                (category, sub_category, measure_type,
                    similarity_function, int(category_order))
                )
        count += 1
        print str(count)
    conn.commit()
    conn.close()

