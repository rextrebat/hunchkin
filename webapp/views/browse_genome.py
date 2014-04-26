#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
from flask import request, g, render_template, Blueprint
from itertools import groupby

browse_genome = Blueprint('browse_genome', __name__)

@browse_genome.route('/browse')
def show_locations():
    return render_template('home.html')


@browse_genome.route('/hotels')
def show_hotels():
    hotels = []
    loc = int(request.args.get("loc"))
    sim = request.args.get("sim", "false")
    loccat = request.args.get("loccat", "false")
    ean = request.args.get("ean", "false")
    db = g.mongo.hotelgenome
    h_query = db.locations.find_one({"loc": loc}, {"query": 1})
    if h_query:
        h_query = h_query["query"]
        h_query = 'db.hotels.find(' + h_query + ')'
        res = eval(h_query)
        hotels = [dict(name=h["name"], h_id=h["hotelId"]) for h in res]
    return render_template('hotels.html',
            hotels=hotels, sim=sim, loccat=loccat, ean=ean)


@browse_genome.route('/genome')
def show_genome():
    genes = []
    cursor = g.db.cursor()
#--------Genes
    cursor.execute(
            """
            SELECT category, sub_category, chromosome, gene_name, bitmask
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
    genome = genome.split(",")
    for gene in all_genes:
        category, sub_category, chromosome, gene_name, bitmask = gene
        genes.append(
                {
                    'category': category,
                    'sub_category': sub_category,
                    'chromosome': chromosome,
                    'gene_name': gene_name.decode("ascii", "ignore"),
                    'value': True if genome[int(bitmask)] >= "1" else False,
                    'raw_value': genome[int(bitmask)]
                    }
                )
#--------Chromosome
    cursor.execute(
            """
            SELECT gc.category, gc.sub_category, gc.chromosome, hc.normalized_score
            FROM hotel_chromosome hc, genome_categories gc
            WHERE hc.chromosome_id = gc.chromosome_id
            AND hotel_id = %s
            ORDER BY normalized_score DESC
            """, h_id
            )
    chromosome_scores=cursor.fetchall()
#--------Sub-category
    cursor.execute(
            """
            SELECT gc.category, gc.sub_category,
            ROUND(AVG(hc.normalized_score),2) as subcat_score
            FROM hotel_chromosome hc, genome_categories gc
            WHERE hc.chromosome_id = gc.chromosome_id
            AND hotel_id = %s
            GROUP by gc.category, gc.sub_category
            ORDER BY subcat_score DESC
            """, h_id
            )
    subcat_scores = cursor.fetchall()
#--------Category
    cursor.execute(
            """
            SELECT gc.category,
            ROUND(AVG(hc.normalized_score),2) as cat_score
            FROM hotel_chromosome hc, genome_categories gc
            WHERE hc.chromosome_id = gc.chromosome_id
            AND hotel_id = %s
            GROUP by gc.category
            ORDER BY cat_score DESC
            """, h_id
            )
    cat_scores = cursor.fetchall()
#--------Name
    cursor.execute(
            """
            SELECT name FROM hotel_basic
            WHERE hotel_id = %s
            """, h_id)
    name = cursor.fetchone()[0]
    return render_template('genome.html',
            genes=genes,
            chromosome_scores=chromosome_scores,
            subcat_scores=subcat_scores,
            cat_scores=cat_scores,
            name=name)


@browse_genome.route('/similar')
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
    if not ids_b:
        ids_b = [999999]
    if not ids_a:
        ids_a = [999999]
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


@browse_genome.route('/loccat')
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

    db = g.mongo.hotelgenome
    res = db.hotel_pois_nokia.find_one({"hotelId": h_id})
    res = res["places"]
    loccat_nokia = [dict(
        name=r["title"],
        category=r["category"]["title"],
        distance=r["distance"]) \
                for r in res if r["type"] == 'urn:nlp-types:place']

    return render_template('loccat.html', 
            loccat=loccat, loccat_nokia=loccat_nokia)


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


@browse_genome.route('/ean_data')
def ean_data():
    h_id = int(request.args.get("h_id"))
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT * FROM activepropertylist
            WHERE EANHotelID = %s
            """, h_id)
    prop_basic = cursor.fetchone()
    cursor.execute(
            """
            SELECT * FROM areaattractionslist
            WHERE EANHotelID = %s
            """, h_id)
    area_attractions = cursor.fetchone()
    if area_attractions:
        area_attractions["AreaAttractions"] = unicode(
                area_attractions["AreaAttractions"], "utf8")
    cursor.execute(
            """
            SELECT * FROM diningdescriptionlist
            WHERE EANHotelID = %s
            """, h_id)
    dining_desc = cursor.fetchone()
    if dining_desc:
        dining_desc["DiningDescription"] = unicode(
                dining_desc["DiningDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM policydescriptionlist
            WHERE EANHotelID = %s
            """, h_id)
    policy_desc = cursor.fetchone()
    if policy_desc:
        policy_desc["PolicyDescription"] = unicode(
                policy_desc["PolicyDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM propertydescriptionlist
            WHERE EANHotelID = %s
            """, h_id)
    prop_desc = cursor.fetchone()
    if prop_desc:
        prop_desc["PropertyDescription"] = unicode(
                prop_desc["PropertyDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM roomtypelist
            WHERE EANHotelID = %s
            """, h_id)
    room_types = cursor.fetchall()
    for r in room_types:
        r["RoomTypeDescription"] = unicode(
                r["RoomTypeDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM spadescriptionlist
            WHERE EANHotelID = %s
            """, h_id)
    spa_desc = cursor.fetchone()
    if spa_desc:
        spa_desc["SpaDescription"] = unicode(
                spa_desc["SpaDescription"], "utf8")
    cursor.execute(
            """
            SELECT AttributeDesc, Type, SubType
            FROM attributelist a, propertyattributelink l
            WHERE a.AttributeID = l.AttributeID
            AND EANHotelID = %s
            ORDER BY Type, SubType
            """, h_id)
    prop_attr = cursor.fetchall()
    for p in prop_attr:
        p["AttributeDesc"] = unicode(p["AttributeDesc"], "utf")
    cursor.execute(
            """
            SELECT AttributeDesc, Type, SubType
            FROM gdsattributelist a, gdspropertyattributelink l
            WHERE a.AttributeID = l.AttributeID
            AND EANHotelID = %s
            ORDER BY Type, SubType
            """, h_id)
    prop_gdsattr = cursor.fetchall()
    for p in prop_gdsattr:
        p["AttributeDesc"] = unicode(p["AttributeDesc"], "utf")
    return render_template('ean_data.html',
            prop_basic=prop_basic,
            area_attractions=area_attractions,
            dining_desc=dining_desc,
            policy_desc=policy_desc,
            prop_desc=prop_desc,
            room_types=room_types,
            spa_desc=spa_desc,
            prop_attr=prop_attr,
            prop_gdsattr=prop_gdsattr,
            )
