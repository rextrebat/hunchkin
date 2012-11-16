#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
from flask import request, g, render_template, Blueprint
import json
import urllib2
import urllib
import genome.genome_distance as genome_distance
import avail.ean_tasks as ean_tasks

search = Blueprint('search', __name__)

@search.route('/')
def show_locations():
    return render_template('search.html')


@search.route('/search')
def search_page():
    return render_template('search.html')


@search.route('/dest_search')
def dest_search():
    search_url = "http://elric:8983/solr/collection1/ac"
    search_params = urllib.urlencode({
        'q': request.args.get("region_startsWith"),
        'wt': 'json',
        'indent': 'true',
        })
    response = urllib2.urlopen(search_url, search_params).read()
    response = json.dumps(json.loads(response)['response'])
    return response


@search.route('/prop_search')
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


@search.route('/search_results')
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
    base_hotel_name = None
    if not comp_hotels:
        errors["region_id"] = "No hotels found for that destination"
    elif len(comp_hotels) > 1000:
        errors["region_id"] = "Too many hotels. Narrow down your destination"
    else:
        result = genome_distance.top_n_similar.delay(
                base_hotel_id,
                comp_hotels,
                10
                )
        similar_hotels = result.get(timeout=10)
        similar_hotel_ids = [s.hotel_id for s in similar_hotels]
        result2 = ean_tasks.get_avail_hotels.delay(
                date_from,
                date_to,
                similar_hotel_ids
                )
        cursor.execute(
                """
                SELECT p.EANHotelID, p.Name, i.ThumbnailURL
                FROM EAN_ActiveProperties p
                LEFT OUTER JOIN EAN_HotelImages i
                ON p.EANHotelID = i.EANHotelID
                AND i.DefaultImage = 1
                WHERE p.EANHotelID in (%s)
                """ % ",".join([str(i) for i in similar_hotel_ids])
                )
        rows = cursor.fetchall()
        hotel_details = {}
        for r in rows:
            hotel_details[r['EANHotelID']] = {
                    'name': r['Name'],
                    'thumbnail_url': r['ThumbnailURL'],
                    }
        hotel_avail = result2.get(timeout=10)
        axes = []
        genome_distance.conn = g.db
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
        base_hotel_name = cursor.fetchone()['Name'].decode('utf-8', 'ignore')
    return render_template('search_results.html',
            axes=axes,
            similar_hotels=similar_hotels,
            hotel_details=hotel_details,
            hotel_avail=hotel_avail,
            base_hotel_name=base_hotel_name,
            base_hotel_id=base_hotel_id,
            errors=errors
            )


@search.route('/get_gene_values')
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
