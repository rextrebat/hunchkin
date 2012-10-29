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

with open("../out/genome.csv") as f:
    cursor.execute(
            """
            DELETE FROM genome_rules
            """
            )
    for r in csv.DictReader(f):
        #if count == 0:
            #count += 1
            #continue
        for k, v in r.iteritems():
            r[k] = v.strip()
        category = r['Category']
        sub_categories = r['Sub-Category']
        bitmask = r['Bitmask']
        gene_name = r['GeneName']
        gene_code = r['GeneCode']
        gene_source = r['GeneSource']
        function = r['Function']
        parameters = r['Parameters']
        for sub_cat in sub_categories.split(","):
            sub_cat = sub_cat.strip()
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

