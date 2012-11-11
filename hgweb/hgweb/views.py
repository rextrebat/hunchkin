#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import pymongo
from flask import request, g, render_template
import json
import urllib2
import urllib
import genome.genome_distance as genome_distance
import avail.ean_tasks as ean_tasks
from hgweb import app

# configuration


@app.template_filter('urlquote')
def urlquote(s):
   return urllib.quote(s)
app.jinja_env.globals['urlquote'] = urlquote


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
    genome_distance.conn = g.db


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
    cursor.execute(
            """
            SELECT name FROM hotel_basic
            WHERE hotel_id = %s
            """, h_id)
    name = cursor.fetchone()[0]
    return render_template('genome.html', genes=genes, name=name)


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


@app.route('/ean_data')
def ean_data():
    h_id = int(request.args.get("h_id"))
    cursor = g.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT * FROM EAN_ActiveProperties
            WHERE EANHotelID = %s
            """, h_id)
    prop_basic = cursor.fetchone()
    cursor.execute(
            """
            SELECT * FROM EAN_AreaAttractions
            WHERE EANHotelID = %s
            """, h_id)
    area_attractions = cursor.fetchone()
    if area_attractions:
        area_attractions["AreaAttractions"] = unicode(
                area_attractions["AreaAttractions"], "utf8")
    cursor.execute(
            """
            SELECT * FROM EAN_DiningDescriptions
            WHERE EANHotelID = %s
            """, h_id)
    dining_desc = cursor.fetchone()
    if dining_desc:
        dining_desc["DiningDescription"] = unicode(
                dining_desc["DiningDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM EAN_PolicyDescriptions
            WHERE EANHotelID = %s
            """, h_id)
    policy_desc = cursor.fetchone()
    if policy_desc:
        policy_desc["PolicyDescription"] = unicode(
                policy_desc["PolicyDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM EAN_PropertyDescriptions
            WHERE EANHotelID = %s
            """, h_id)
    prop_desc = cursor.fetchone()
    if prop_desc:
        prop_desc["PropertyDescription"] = unicode(
                prop_desc["PropertyDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM EAN_RoomTypes
            WHERE EANHotelID = %s
            """, h_id)
    room_types = cursor.fetchall()
    for r in room_types:
        r["RoomTypeDescription"] = unicode(
                r["RoomTypeDescription"], "utf8")
    cursor.execute(
            """
            SELECT * FROM EAN_SpaDescriptions
            WHERE EANHotelID = %s
            """, h_id)
    spa_desc = cursor.fetchone()
    if spa_desc:
        spa_desc["SpaDescription"] = unicode(
                spa_desc["SpaDescription"], "utf8")
    cursor.execute(
            """
            SELECT AttributeDesc, Type, SubType
            FROM EAN_Attributes a, EAN_PropertyAttributeLink l
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
            FROM EAN_GDSAttributes a, EAN_GDSPropertyAttributeLink l
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


@app.route('/search')
def search():
    return render_template('search.html')


@app.route('/dest_search')
def dest_search():
    search_url = "http://elric:8983/solr/collection1/ac"
    search_params = urllib.urlencode({
        'q': request.args.get("region_startsWith"),
        'wt': 'json',
        'indent': 'true',
        })
    #response = json.loads(urllib2.urlopen(search_url, search_params).read())
    #region_names = [r["name"] for r in response['response']['docs']]
    #return json.dumps(region_names)
    response = urllib2.urlopen(search_url, search_params).read()
    response = json.dumps(json.loads(response)['response'])
    return response


@app.route('/prop_search')
def prop_search():
    search_url = "http://elric:8983/solr/properties/ac"
    search_params = urllib.urlencode({
        'q': request.args.get("prop_startsWith"),
        'wt': 'json',
        'indent': 'true',
        })
    response = urllib2.urlopen(search_url, search_params).read()
    response = json.dumps(json.loads(response)['response'])
    return response


@app.route('/search_results')
def handle_search():
    region_id = int(request.args.get("dest_id"))
    base_hotel_id = int(request.args.get("hotel_id"))
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    cursor = g.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT rp.EANHotelID 
            FROM EAN_RegionPropertyMapping rp, EAN_ActiveProperties p
            WHERE p.EANHotelID = rp.EANHotelID
            AND rp.RegionID = "%s"
            """, region_id
            )
    rows = cursor.fetchall()
    comp_hotels = [int(r['EANHotelID']) for r in rows]
    errors = {}
    similar_hotels = None
    hotel_details = None
    hotel_avail = None
    axes = None
    if not comp_hotels:
        errors["region_id"] = "No hotels found for that destination"
    elif len(comp_hotels) > 500:
        errors["region_id"] = "Too many hotels. Narrow down your destination"
    else:
        result = genome_distance.top_n_similar.delay(
                base_hotel_id,
                comp_hotels,
                10
                )
        similar_hotels = result.get(timeout=5)
        similar_hotel_ids = [s.hotel_id for s in similar_hotels]
        result2 = ean_tasks.get_avail_hotels.delay(
                date_from,
                date_to,
                similar_hotel_ids
                )
        cursor.execute(
                """
                SELECT p.EANHotelID, p.Name, i.ThumbnailURL
                FROM EAN_ActiveProperties p, EAN_HotelImages i
                WHERE p.EANHotelID = i.EANHotelID
                AND i.DefaultImage = 1
                AND p.EANHotelID in (%s)
                """ % ",".join([str(i) for i in similar_hotel_ids])
                )
        rows = cursor.fetchall()
        hotel_details = {}
        for r in rows:
            hotel_details[r['EANHotelID']] = {
                    'name': r['Name'],
                    'thumbnail_url': r['ThumbnailURL'],
                    }
        hotel_avail = result2.get(timeout=5)
        axes = []
        for k, v in genome_distance.get_axes().iteritems():
            category, sub_category = k.split("|")
            category_order = v['category_order']
            axes.append((category, sub_category, category_order))
            axes.sort(key=lambda a: a[2])
        cursor.execute(
                """
                SELECT Name
                FROM EAN_ActiveProperties
                WHERE EANHotelID = %s
                """, base_hotel_id
                )
        base_hotel_name = cursor.fetchone()['Name']
    return render_template('search_results.html',
            axes=axes,
            similar_hotels=similar_hotels,
            hotel_details=hotel_details,
            hotel_avail=hotel_avail,
            base_hotel_name=base_hotel_name,
            base_hotel_id=base_hotel_id,
            errors=errors
            )


@app.route('/get_gene_values')
def get_gene_values():
    base_hotel_id = int(request.args.get("base_hotel_id"))
    comp_hotel_id = int(request.args.get("comp_hotel_id"))
    category = request.args.get("category").strip()
    sub_category = request.args.get("sub_category").strip()
    result = genome_distance.get_gene_values.delay(
            base_hotel_id, comp_hotel_id, category, sub_category)
    gene_values = result.get(timeout=5)
    return render_template('gene_values.html', 
            gene_values=gene_values)


@app.route('/test_form')
def test_form():
    print request.form
    test_val = request.args.get("test")
    return "I got %s" % test_val


if __name__ == '__main__':
    app.run(host="0.0.0.0")