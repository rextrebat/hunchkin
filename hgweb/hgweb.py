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
    sim = request.args.get("sim", "false")
    db = g.mongo.hotelgenome
    h_query = db.locations.find_one({"loc": loc}, {"query": 1})
    if h_query:
        h_query = h_query["query"]
        h_query = 'db.hotels.find(' + h_query + ')'
        res = eval(h_query)
        hotels = [dict(name=h["name"], h_id=h["hotelId"]) for h in res]
    return render_template('hotels.html', hotels=hotels, sim=sim)


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


@app.route('/similar')
def similar_hotels():
    comp_hotel = int(request.args.get("h_id"))
    cursor = g.db.cursor()
    cursor.execute(
            """
            SELECT hotel_b, sim_score
            FROM top_similar_hotels
            WHERE hotel_a = %s
            ORDER BY sim_score DESC
            """, (comp_hotel)
            )
    res = cursor.fetchall()
    ids = [r[0] for r in res]
    hotels = [dict(h_id=r[0], score=r[1]) for r in res]
    db = g.mongo.hotelgenome
    res2 = db.hotels.find({"hotelId": {"$in": ids}})
    names = [dict(h_id=r["hotelId"],name=r["name"]) for r in res2]
    for i, h in enumerate(hotels):
        for r in names:
            if h["h_id"] == r["h_id"]:
                hotels[i]["name"] = r["name"]
    return render_template('similar_hotels.html',
            hotels=hotels, comp_hotel=comp_hotel)



    



if __name__ == '__main__':
    app.run(host="0.0.0.0")
