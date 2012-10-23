#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Store Genome Rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import csv
import MySQLdb
import re


conn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
        )

cursor = conn.cursor()
match_re = re.compile('match\("(.*)"')

count = 0

with open("out/genome.csv") as f:
    cursor.execute(
            """
            DELETE FROM genome_rules
            """
            )
    for r in csv.reader(f):
        if count == 0:
            count += 1
            continue
        r = [c.strip() for c in r]
        category = r[0]
        sub_categories = r[1]
        bitmask = r[2]
        gene_name = r[3]
        gene_code = r[10]
        gene_source = r[11]
        function = r[12]
        parameters = r[13]
        for sub_cat in sub_categories.split(","):
            cursor.execute(
                    """
                    INSERT INTO genome_rules 
                    (
                    category, sub_category, gene_name, gene_code,
                    bitmask, gene_source, function, parameters
                    )
                    VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (category, sub_cat, gene_name, gene_code,
                        int(bitmask), gene_source, function, parameters)
                    )
        count += 1
        print str(count)
    conn.commit()
    conn.close()

