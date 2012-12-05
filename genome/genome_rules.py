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

with open("../out/genome.csv") as f:
    cursor.execute(
            """
            DELETE FROM genome_rules
            """
            )
    for r in csv.DictReader(f):
        for k, v in r.iteritems():
            r[k] = v.strip()
        category = r['Category']
        sub_category = r['SubCategory']
        chromosome = r['Chromosome']
        usage = r['Usage']
        bitmask = r['Bitmask']
        gene_name = r['GeneName']
        gene_code = r['GeneCode']
        gene_source = r['GeneSource']
        function = r['Function']
        parameters = r['Parameters']
        weight = r['Weight']
        cursor.execute(
                """
                INSERT INTO genome_rules
                (
                category, sub_category, chromosome, gene_usage,
                gene_name, gene_code,
                bitmask, gene_source,
                function, parameters, weight
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (category, sub_category, chromosome, usage,
                    gene_name, gene_code,
                    int(bitmask), gene_source,
                    function, parameters, int(weight))
                )
        count += 1
        print str(count)
    conn.commit()
    conn.close()

