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
import genome.chromosome_distance as chromosome_distance
import avail.ean_tasks as ean_tasks

search = Blueprint('search', __name__)

@search.route('/')
def index():
    return render_template('search.html')


@search.route('/search')
def index():
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


def get_sub_category_list(sim):
    """
    Return two lists
    """
    pass


@search.route('/search_results_c')
def handle_search_c():
    show_view = request.args.get("show_view", "")
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
    hotel_recos = []
    similar_hotels = None
    hotel_avail = None
    hotel_dict = {}
    base_hotel_name = None
    categories = ["STAR RATING", "HOTEL FEATURES", "HOTEL DINING", 
            "ROOM FEATURES", "LOCATION"]
    top_sub_cat = 2
    top_chromosomes = 2
    if not comp_hotels:
        errors["region_id"] = "No hotels found for that destination"
    elif len(comp_hotels) > 1000:
        errors["region_id"] = "Too many hotels. Narrow down your destination"
    else:
        result = chromosome_distance.top_n_similar.apply_async((
                base_hotel_id,
                comp_hotels,
                5
                ), queue="distance")
        similar_hotels = result.get(timeout=10)
        similar_hotel_ids = [s[0] for s in similar_hotels]
        result2 = ean_tasks.get_avail_hotels.apply_async((
                date_from,
                date_to,
                similar_hotel_ids
                ), queue="avail")
        for s in similar_hotels:
            hotel_dict[s[0]] = dict(
                    hotel_id=s[0],
                    aggregate=s[1],
                    categories=[],
                    category_scores=[]
                    )
            for cat in s[2]:
                if cat[0] == "STAR RATING":
                    continue
                hotel_dict[s[0]]["category_scores"].append(
                        round(cat[1] * 100))
                positive = []
                for sc in cat[2][:top_sub_cat]:
                    positive_s = []
                    for ch in sc[2][:top_chromosomes]:
                        positive_s.append(ch[0])
                    if positive_s:
                        positive.append(" and ".join(positive_s))
                negative = []
                for sc in cat[2][-top_sub_cat:]:
                    negative_s = []
                    for ch in sc[2][-top_chromosomes:]:
                        negative_s.append(ch[0])
                    if negative_s:
                        negative.append(" and ".join(negative_s))
                hotel_dict[s[0]]["categories"].append(dict(
                    category_name=cat[0],
                    positive=positive,
                    negative=negative,
                    ))
        # Get Hotel Details
        cursor.execute(
                """
                SELECT p.EANHotelID, p.Name, p.StarRating, i.ThumbnailURL,
                p.Latitude, p.Longitude
                FROM EAN_ActiveProperties p
                LEFT OUTER JOIN EAN_HotelImages i
                ON p.EANHotelID = i.EANHotelID
                AND i.DefaultImage = 1
                WHERE p.EANHotelID in (%s)
                """ % ",".join([str(i) for i in similar_hotel_ids])
                )
        rows = cursor.fetchall()
        for r in rows:
            hotel_dict[r['EANHotelID']]['name'] = r['Name']
            hotel_dict[r['EANHotelID']]['star_rating'] = r['StarRating']
            hotel_dict[r['EANHotelID']]['star_value'] = str(r[
                'StarRating']) + " Stars"
            hotel_dict[r['EANHotelID']]['thumbnail_url'] = r[
                    'ThumbnailURL']
            hotel_dict[r['EANHotelID']]['Latitude'] = r['Latitude']
            hotel_dict[r['EANHotelID']]['Longitude'] = r['Longitude']
        hotel_avail = result2.get(timeout=10)
        for k, v in hotel_avail.iteritems():
            hotel_dict[k] = dict(hotel_dict[k].items() + v.items())
        hotel_recos = hotel_dict.values()
        hotel_recos.sort(key=lambda h:h["aggregate"], reverse=True)
        for i,h in enumerate(hotel_recos, start=1):
            h['index_img'] = "orange0" + str(i) + ".png"
        cat_score_min = min(
                [min(h["category_scores"]) for h in hotel_recos])
        cat_score_max = max(
                [max(h["category_scores"]) for h in hotel_recos])
        cursor.execute(
                """
                SELECT Name
                FROM EAN_ActiveProperties
                WHERE EANHotelID = %s
                """, base_hotel_id
                )
        base_hotel_name = cursor.fetchone()['Name'].decode('utf-8', 'ignore')
        #Get co-ordinates for region and each hotel
        cursor.execute(
                """
                SELECT CenterLatitude, CenterLongitude
                FROM EAN_RegionCenterCoordinates
                WHERE RegionID = %s
                """, region_id)
        r = cursor.fetchone()
        if r:
            r_lat, r_long = r['CenterLatitude'], r['CenterLongitude']
        else:
            r_lat, r_long = 0, 0

# Save the session
    session = request.environ['beaker.session']
    session['search_result_sim'] = similar_hotels
    session['hotel_info'] = hotel_dict
    session.save()

    if show_view.lower() == "g":
        template = "search_results_g.html"
    elif show_view.lower() == "m":
        template = "search_results_m.html"
    else:
        template = "search_results_c.html"
    return render_template(template,
            hotel_recos=hotel_recos,
            category_scores_range=[cat_score_min, cat_score_max],
            base_hotel_name=base_hotel_name,
            base_hotel_id=base_hotel_id,
            region_lat=r_lat,
            region_long=r_long,
            errors=errors
            )


@search.route('/hotel_compare')
def hotel_compare():
    session = request.environ['beaker.session']
    if not session.has_key('search_result_sim'):
        return "Invalid session. Try again"
    similar_hotels = session['search_result_sim']
    similar_hotel_ids = [s[0] for s in similar_hotels]
    result = chromosome_distance.get_gene_values.apply_async(args=[
            similar_hotel_ids], queue="distance")
    subcats, hotel_genes = result.get(timeout=10)
    hotel_dict = session['hotel_info']
    return render_template(
            "subcat_gene_values.html",
            similar_hotel_ids=similar_hotel_ids,
            subcats=subcats,
            hotel_dict=hotel_dict,
            hotel_genes=hotel_genes,
            )
