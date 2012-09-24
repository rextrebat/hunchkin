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
    loccat = request.args.get("loccat", "false")
    db = g.mongo.hotelgenome
    h_query = db.locations.find_one({"loc": loc}, {"query": 1})
    if h_query:
        h_query = h_query["query"]
        h_query = 'db.hotels.find(' + h_query + ')'
        res = eval(h_query)
        hotels = [dict(name=h["name"], h_id=h["hotelId"]) for h in res]
    return render_template('hotels.html',
            hotels=hotels, sim=sim, loccat=loccat)


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
            SELECT s.hotel_b, h.name, s.sim_score
            FROM hotel_basic h, top_similar_hotels s
            WHERE s.hotel_a = %s
            AND h.hotel_id = s.hotel_b
            ORDER BY s.sim_score DESC
            """, (comp_hotel)
            )
    res = cursor.fetchall()
    hotels = [dict(h_id=r[0], name=r[1], score=r[2]) for r in res]
    ids_b = [r[0] for r in res if r[0] > comp_hotel]
    ids_a = [r[0] for r in res if r[0] < comp_hotel]
    in_b = ",".join(map(str, ids_b))
    in_a = ",".join(map(str, ids_a))
    cursor.execute(
            """
            SELECT hotel_b as h_id, sim_axis, sim_value
            FROM hotel_similarity
            WHERE hotel_a = %s
            AND hotel_b IN (%s)
            UNION
            SELECT hotel_a as h_id, sim_axis, sim_value
            FROM hotel_similarity
            WHERE hotel_b = %s
            AND hotel_a IN (%s)
            """ % (comp_hotel, in_b, comp_hotel, in_a))
    res = cursor.fetchall()
    sim = {}
    for r in res:
        h_id, sim_axis, sim_value = r
        if h_id not in sim:
            sim[h_id] = {}
        sim[h_id][sim_axis] = sim_value
    cursor.execute(
            """
            SELECT DISTINCT category, sub_category
            FROM genome_rules
            """
            )
    res = cursor.fetchall()
    axes=[dict(category=r[0], sub_category=r[1]) for r in res]
    cursor.execute(
            """
            SELECT name FROM hotel_basic
            WHERE hotel_id = %s
            """ % comp_hotel)
    comp_hotel_name = cursor.fetchone()[0]
    return render_template('similar_hotels.html',
            hotels=hotels,
            sim=sim,
            axes=axes,
            comp_hotel=comp_hotel,
            comp_hotel_name=comp_hotel_name
            )


@app.route('/loccat')
def hotel_loc():
    h_id = int(request.args.get("h_id"))
    cursor = g.db.cursor()
    cursor.execute(
            """
            SELECT category, count
            FROM loc_categories
            WHERE hotel_id = %s
            """ % h_id
            )
    res = cursor.fetchall()
    loccat = [dict(category=r[0], count=r[1]) for r in res]
    return render_template('loccat.html', 
            loccat=loccat)


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


if __name__ == '__main__':
    app.run(host="0.0.0.0")
