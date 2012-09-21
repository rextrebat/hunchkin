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
        category, sub_category, bitmask, gene_name, comment, subjective, \
          no_reviews, from_expedia, gene_code, key, attr, func, ign1, ign2 = r
        if func == "compare":
            gene_rule = 'compare("' + attr + '", "' + key + '")'
        elif func[:5] == "match":
            param = match_re.match(func).group(1)
            if param == "...":
                gene_rule = 'match("' + attr + '", "' + key + '")'
            else:
                gene_rule = 'match("' + attr + '", "' + param + '")'
        else:
            gene_rule = ''
        cursor.execute(
                """
                INSERT INTO genome_rules 
                (
                category, sub_category, gene_name, comment, subjective,
                no_reviews, from_expedia, gene_code, gene_rule, bitmask
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (category, sub_category, gene_name, comment, subjective,
                    no_reviews, from_expedia, gene_code,
                    gene_rule, int(bitmask))
                )
        count += 1
        print str(count)
    conn.commit()
    conn.close()

