#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import pymongo
from flask import Flask, request, session, g, redirect, url_for, \
        abort, render_template, flash

# configuration
DEBUG = True
SECRET_KEY = "development key"
HOST="localhost"
USERNAME = "appuser"
PASSWORD = "rextrebat"
DB = "hotel_genome"


app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return MySQLdb.Connection(
            host=app.config['HOST'],
            db=app.config['DB'],
            user=app.config['USERNAME'],
            passwd=app.config['PASSWORD']
            )

def connect_mongo():
    return pymongo.Connection(host=app.config['HOST'])


@app.before_request
def before_request():
    g.db = connect_db()
    g.mongo = connect_mongo()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
def show_locations():
    return render_template('home.html')


@app.route('/hotels')
def show_hotels():
    hotels = []
    loc = int(request.args.get("loc"))
    db = g.mongo.hotelgenome
    h_query = db.locations.find_one({"loc": loc}, {"query": 1})
    if h_query:
        h_query = h_query["query"]
        h_query = 'db.hotels.find(' + h_query + ')'
        res = eval(h_query)
        hotels = [dict(name=h["name"], h_id=h["hotelId"]) for h in res]
    return render_template('hotels.html', hotels=hotels)


@app.route('/genome')
def show_genome():
    genes = []
    cursor = g.db.cursor()
    cursor.execute(
            """
            SELECT category, sub_category, gene_name, bitmask
            FROM genome_rules
            ORDER BY bitmask
            """
            )
    all_genes = cursor.fetchall()
    h_id = int(request.args.get("h_id"))
    cursor.execute(
            """
            SELECT genome FROM hotel_genome
            WHERE hotel_id = %s
            """, h_id
            )
    genome = cursor.fetchone()[0]
    for gene in all_genes:
        category, sub_category, gene_name, bitmask = gene
        genes.append(
                {
                    'category': category,
                    'sub_category': sub_category,
                    'gene_name': gene_name.decode("ascii", "ignore"),
                    'value': True if genome[int(bitmask)] == "1" else False
                    }
                )
    return render_template('genome.html', genes=genes)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
