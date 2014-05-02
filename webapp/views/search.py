#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

logger = logging.getLogger("search")

from sets import Set
import MySQLdb
from flask import request, g, render_template, Blueprint, current_app
import simplejson as json
import urllib2
import urllib
import numpy
import scipy.stats
import bisect
import genome.genome_distance as genome_distance
import genome.chromosome_distance as chromosome_distance
import avail.ean_tasks as ean_tasks

search = Blueprint('search', __name__)

@search.route('/search')
@search.route('/')
def index():
    return render_template('search.html')


@search.route('/dest_search')
def dest_search():
    search_url_base = current_app.config['SEARCH_URL_BASE']
    search_url = search_url_base + "collection1/ac"
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
    search_url_base = current_app.config['SEARCH_URL_BASE']
    search_url = search_url_base + "properties/ac"
    search_params = urllib.urlencode({
        'q': request.args.get("prop_startsWith"),
        'wt': 'json',
        'indent': 'true',
        })
    response = urllib2.urlopen(search_url, search_params).read()
    response = json.dumps(json.loads(response)['response'])
    return response


@search.route('/get_gene_values')
def get_gene_values():
    base_hotel_id = int(request.args.get("base_hotel_id"))
    comp_hotel_id = int(request.args.get("comp_hotel_id"))
    category = request.args.get("category").strip()
    sub_category = request.args.get("sub_category").strip()
    result = genome_distance.get_gene_values.delay(
            base_hotel_id, comp_hotel_id, category, sub_category)
    gene_values = result.get(timeout=10)
    return render_template('gene_values.html', 
            gene_values=gene_values)

# ------- Search Functions ------------

def search_get_hotels(region_id):
    """
    get all the hotels for this region_id 
    and cache it if not in cache
    """
    mc = g.mc
    key = "hotels_in_region_" + str(region_id)
    hotels_in_region = mc.get(key)
    if not hotels_in_region:
        cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(
                """
                    SELECT rp.EANHotelID, p.Name, p.StarRating,
                    i.ThumbnailURL, p.Latitude, p.Longitude, p.LowRate
                    FROM regioneanhotelidmapping rp
                    JOIN activepropertylist p
                    ON rp.EANHotelID = p.EANHotelID
                    LEFT OUTER JOIN hotelimagelist i
                    ON rp.EANHotelID = i.EANHotelID
                    AND i.DefaultImage = 1
                    WHERE rp.RegionID = "%s"
                """, region_id
                )
        rows = cursor.fetchall()
        hotels_in_region = {}
        for r in rows:
            hotels_in_region[r["EANHotelID"]] = r
        mc.set(key, hotels_in_region, 7200)
#TODO: parameterize expiration
    return hotels_in_region


def search_consideration_set(all_hotels, ref_hotel_id):
    """
    create consideration set of hotels based ON
    price percentile of reference hotel
    20 items on either side of percentile point
    """
#TODO: Magic to be fixed
    NUM_HOTELS = 40
    ref_pc = get_ref_hotel_price_percentile(ref_hotel_id)
    hotels_and_rates = sorted(
            [(k, v["LowRate"]) for k, v in all_hotels.iteritems()],
            key = lambda h: h[1])
    rates = [h_lowrate for (h_id, h_lowrate) in hotels_and_rates]
    rate_percentiles = [
            scipy.stats.percentileofscore(rates, h_lowrate)
            for h_lowrate in rates]
    pos = bisect.bisect(rate_percentiles, ref_pc)
    consideration_set = Set()
    l = len(hotels_and_rates)
    for i in range(0 if pos - NUM_HOTELS/2 < 0 else pos - NUM_HOTELS/2, pos):
        consideration_set.add(hotels_and_rates[i][0])
    for i in range(pos, l if pos + NUM_HOTELS/2 > l else pos + NUM_HOTELS/2):
        consideration_set.add(hotels_and_rates[i][0])
    logger.debug("Consideration Set: %s" % str(len(consideration_set)))
    return consideration_set



def search_get_similarities(region_id, base_hotel_id, comp_hotels):
    """
    get similarities for this base_hotel_id and region_id
    """
    mc = g.mc
    key = "similarities_" + str(region_id) + "_" + str(base_hotel_id)
    similarities = mc.get(key)
    if not similarities:
        similarities = search_get_hotel_distances(
                search_post_hotel_distances(base_hotel_id, comp_hotels))
        #mc.set(key, similarities, 3600)
    return similarities


def search_post_hotel_distances(base_hotel_id, comp_hotels):
    result = chromosome_distance.top_n_similar.apply_async((
            base_hotel_id,
            comp_hotels
            ), queue="distance")
    return result


def search_get_hotel_distances(dist_handle):
    similar_hotels = dist_handle.get(timeout=30)
    return similar_hotels
#TODO: parameterize timeout


def search_add_availibility(date_from, date_to, hotel_recommendations):
    """
    add availibility information to recommendations
    """
    recommended_ids = [h["hotel_id"] for h in hotel_recommendations]
    availabilities = search_get_avail(
            search_post_avail(date_from, date_to, recommended_ids))
    for k, v in availabilities.iteritems():
        for i, ri in enumerate(recommended_ids):
            if k == ri:
                hotel_recommendations[i] = dict(
                        hotel_recommendations[i].items() + v.items()
                        )


def search_post_avail(date_from, date_to, similar_hotel_ids):
    result = ean_tasks.get_avail_hotels.apply_async((
            date_from,
            date_to,
            similar_hotel_ids
            ), queue="avail")
    return result


def search_get_avail(avail_handle):
    hotel_avail = avail_handle.get(timeout=20)
#TODO: parameterize timeout
    return hotel_avail


def search_filter_price_range(all_hotels, selected_hotel_ids,
        rate_range_low, rate_range_high):
    """
    filter out hotels not within this range
    """
    for h in selected_hotel_ids:
        if not rate_range_low <= all_hotels[h]["LowRate"] <= rate_range_high:
            selected_hotel_ids.remove(h)
    return


def search_prepare_selection(all_hotels, similarities,
        selected_hotel_ids, n_limit):
    """
    Prepare selection for display
    """
#TODO: parameterize following constants
    top_sub_cat = 2
    top_chromosomes = 2

    hotel_recommendations = []
    n = 0
    for s in similarities:
        if n == n_limit:
            break
        if s[0] not in selected_hotel_ids:
            continue
        hotel = dict(
                hotel_id = s[0],
                aggregates = s[1],
                categories = [],
                category_scores = []
                )
        for cat in s[2]:
            if cat[0] == "STAR RATING":
                continue
            hotel["category_scores"].append(
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
            hotel["categories"].append(dict(
                category_name=cat[0],
                positive=positive,
                negative=negative,
                ))
            hotel = dict(
                    hotel.items() + all_hotels[s[0]].items()
                    )
            hotel["array_offset"] = n
        n += 1
        hotel_recommendations.append(hotel)
    return hotel_recommendations


def get_hotel_name(hotel_id):
    """
    return hotel_name given id
    """
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT Name
            FROM activepropertylist
            WHERE EANHotelID = %s
            """, hotel_id
            )
    return cursor.fetchone()['Name'].decode('utf-8', 'ignore')


def get_region_lat_long(region_id):
    """
    Return center of region given region_id
    """
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT CenterLatitude, CenterLongitude
            FROM regioncentercoordinateslist
            WHERE RegionID = %s
            """, region_id)
    r = cursor.fetchone()
    if r:
        r_lat, r_long = r['CenterLatitude'], r['CenterLongitude']
    else:
        r_lat, r_long = 0, 0
    return r_lat, r_long


def get_ref_hotel_price_percentile(ref_hotel_id):
    """
    Return the percentile score of the price of the ref hotel
    in its region
    """
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT b.LowRate
            FROM activepropertylist a, activepropertylist b
            WHERE a.RegionID = b.RegionID
            AND a.EANHotelID = %s
            """, ref_hotel_id)
    ref_rates = [float(r['LowRate']) for r in cursor.fetchall()]
    cursor.execute(
            """
            SELECT LowRate
            FROM activepropertylist
            WHERE EANHotelID = %s
            """, ref_hotel_id)
    ref_hotel_low_rate = cursor.fetchone()['LowRate']
    return scipy.stats.percentileofscore(ref_rates,ref_hotel_low_rate)


def get_initial_price_limit(ref_hotel_id, region_id):
    """
    Find the initial price limit:
    1. Find percentile score of price of ref_hotel_id in its region
    2. Determine what is the equivalent percentile rate in the search region
    3. Add 100% (configurable) to that
    """
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    ref_pc = get_ref_hotel_price_percentile(ref_hotel_id)
    cursor.execute(
            """
            SELECT p.LowRate
            FROM regioneanhotelidmapping rp
            JOIN activepropertylist p
            ON rp.EANHotelID = p.EANHotelID
            WHERE rp.RegionID = %s
            """, region_id)
    search_rates = [float(r['LowRate']) for r in cursor.fetchall()]
# TODO: Parameterize the following:
    price_limit_mult = 2.0
    logger.debug("search_rates length: %s" % str(len(search_rates)))
    logger.debug("ref_pc: %s" % str(ref_pc))
    return numpy.percentile(search_rates, ref_pc) * price_limit_mult


def get_region_name(region_id):
    """
    Return region name given region_id
    """
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT RegionName
            FROM parentregionlist
            WHERE RegionID = %s
            """, region_id)
    return cursor.fetchone()['RegionName'].decode('utf-8', 'ignore')


def get_result_template(show_view):
    """
    return template
    """
    if show_view.lower() == "g":
        template = "search_results_g.html"
    elif show_view.lower() == "m":
        template = "search_results_m.html"
    else:
        template = "search_results_c.html"
    return template


@search.route('/search_results')
def handle_search():

#1. Get request parameters
    show_view = request.args.get("show_view", "")
    region_id = int(request.args.get("dest_id"))
    base_hotel_id = int(request.args.get("hotel_id"))
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    rate_range_low = request.args.get("rate_range_low", 0)
    rate_range_high = request.args.get("rate_range_high", 100000)
#TODO: parameterize


#2. Get candidate hotels
    all_hotels = search_get_hotels(region_id)
    all_hotel_ids = [int(h) for h in all_hotels.iterkeys()]
#TODO: bail out if too few or too many hotels

#3. Post similarities request
    similarities = search_get_similarities(
            region_id,
            base_hotel_id,
            all_hotel_ids
            )

#4. Apply Filters
    selected_hotel_ids = Set(all_hotel_ids)
    search_filter_price_range(all_hotels, selected_hotel_ids,
            rate_range_low, rate_range_high)


#5. Prepare Selection
    recommendations = search_prepare_selection(
            all_hotels,
            similarities,
            selected_hotel_ids,
            5
            )
#TODO: parameterize number in selection

#6. Get availability
    search_add_availibility(date_from, date_to, recommendations)

#7. Add pins for recommendations
    for i,h in enumerate(recommendations, start=1):
        h["index_img"] = "orange0" + str(i) + ".png"

#8. Get base_hotel_name
    base_hotel_name = get_hotel_name(base_hotel_id)

#9. Get region lat long
    region_lat, region_long = get_region_lat_long(region_id)

#10. Save session
    session = request.environ['beaker.session']
    session['search_result_sim'] = similarities
    session['hotel_info'] = recommendations
    session.save()

#11. Get result template
    template = get_result_template(show_view)

#11. Render
    return render_template(template,
            hotel_recos=recommendations,
            base_hotel_name=base_hotel_name,
            base_hotel_id=base_hotel_id,
            region_lat=region_lat,
            region_long=region_long,
            errors={}
            )


@search.route('/search_results_a')
def handle_search_a():
    region_id = int(request.args.get("dest_id"))
    base_hotel_id = int(request.args.get("hotel_id"))
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    base_hotel_name = get_hotel_name(base_hotel_id)
    region_name = get_region_name(region_id)
    return render_template(
            "search_results_a.html",
            region_id=region_id,
            base_hotel_id=base_hotel_id,
            date_from=date_from,
            date_to=date_to,
            base_hotel_name=base_hotel_name,
            region_name=region_name,
            )


@search.route('/search_results_a_ctrl')
def handle_search_a_ctrl():
    """
    Angular.js based search  return json
    """
#1. Get request parameters
    region_id = int(request.args.get("dest_id"))
    base_hotel_id = int(request.args.get("hotel_id"))
#TODO: parameterize

#2. Get candidate hotels
    all_hotels = search_get_hotels(region_id)
#TODO: bail out if too few or too many hotels


#3. Narrow consideration set based on price percentile of ref hotel
    consideration_set = search_consideration_set(all_hotels, base_hotel_id)

#4. Post similarities request
    similarities = search_get_similarities(
            region_id,
            base_hotel_id,
            consideration_set
            )

#5. Prepare Selection
    recommendations = search_prepare_selection(
            all_hotels,
            similarities,
            consideration_set,
            200
            )
#TODO: parameterize number in selection
    return json.dumps(recommendations)


@search.route('/search_results_avail')
def handle_search_avail():
    """
    Return Availability for hotel set
    """
#1. Get request parameters
    hotel_ids = request.args.get("hotel_ids")
    hotel_ids = [int(h) for h in hotel_ids.split(",")]
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    availabilities = search_get_avail(
            search_post_avail(date_from, date_to, hotel_ids))

    return json.dumps(availabilities, use_decimal=True)


@search.route('/search_results_a_region_coords')
def handle_search_a_region_coords():
    """
    Return region latitude, Longitude
    """
    region_id = int(request.args.get("region_id"))
    region_lat, region_long = get_region_lat_long(region_id)
    return json.dumps(
            dict(
                latitude=region_lat,
                longitude=region_long
                ), use_decimal=True
            )


@search.route('/search_results_a_initial_price_limit')
def handle_search_a_initial_price_limit():
    """
    Return initial price limit
    """
    region_id = int(request.args.get("region_id"))
    ref_hotel_id = int(request.args.get("ref_hotel_id"))
    return json.dumps(
            get_initial_price_limit(ref_hotel_id, region_id),
            use_decimal=True
            )


# ------- Search Functions ------------


@search.route('/search_results_c')
def handle_search_c():
    show_view = request.args.get("show_view", "")
    region_id = int(request.args.get("dest_id"))
    base_hotel_id = int(request.args.get("hotel_id"))
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    cursor = g.db_ean.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(
            """
            SELECT rp.EANHotelID 
            FROM regioneanhotelidmapping rp, activepropertylist p
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
        similar_hotels = result.get(timeout=30)
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
                FROM activepropertylist p
                LEFT OUTER JOIN hotelimagelist i
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
        hotel_avail = result2.get(timeout=20)
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
                FROM activepropertylist
                WHERE EANHotelID = %s
                """, base_hotel_id
                )
        base_hotel_name = cursor.fetchone()['Name'].decode('utf-8', 'ignore')
        #Get co-ordinates for region and each hotel
        cursor.execute(
                """
                SELECT CenterLatitude, CenterLongitude
                FROM regioncentercoordinateslist
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
    subcats, hotel_genes = result.get(timeout=20)
    hotel_dict = session['hotel_info']
    return render_template(
            "subcat_gene_values.html",
            similar_hotel_ids=similar_hotel_ids,
            subcats=subcats,
            hotel_dict=hotel_dict,
            hotel_genes=hotel_genes,
            )
