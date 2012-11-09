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

attr_ids = set(())


with open("../out/genome.csv") as f:
    for r in csv.DictReader(f):
        for k, v in r.iteritems():
            r[k] = v.strip()
        function = r['Function']
        parameters = r['Parameters']
        if function.strip() == "compare":
            attrs = parameters.split("|")[1]
        elif function.strip() == "exist":
            attrs = parameters
        else:
            attrs = ""
        for a in attrs.strip().split(","):
            if a:
                attr_ids.add(int(a))

    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT AttributeID, AttributeDesc, Type
            FROM EAN_Attributes
            """
            )
    rows = cursor.fetchall()
    for r in rows:
        a_id, a_desc, a_type = r
        if a_type == "Policy":
            continue
        if a_id not in attr_ids:
            print "%d,%s" % (a_id, a_desc)
    conn.close()

