#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google Places - Get Nearby Places"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import pymongo
import time

import crawl_helper


logger = logging.getLogger('ean_hotel_desc')

# -- globals
conn = pymongo.Connection("localhost", 27017)
db = conn.hotelgenome

throttler1 = crawl_helper.Throttler(95000, 86400)

base_url = "https://maps.googleapis.com/maps/api/place/search/json"

base_params = {
        "key": "AIzaSyBxpxs48G5HgdS-yaAAYyLP1LL86pmslMQ",
        "radius": "2000",
        "sensor": "false",
        }

config_places = crawl_helper.FetcherConfig(
        base_url=base_url,
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.JSON
        )

fetcher_pool = crawl_helper.FetcherPool(
        size=5,
        throttlers=[throttler1]
        )


def handle_places_response(response, context):
    """
    handler - response to places search
    """
    if "next_page_token" in response:
        next_page_token = response["next_page_token"]
    else:
        next_page_token = None
    places = response["results"]
    response = {}
    response["hotelId"] = context["hotelId"]
    response["places"] = places
    try:
        rec = db.hotel_pois.find_one({"hotelId": response["hotelId"]})
        if not rec:
            logger.debug("inserting hotel id %s" % (response["hotelId"]))
            db.hotel_pois.insert(response)
        else:
            logger.debug("updating hotel id %s" % (response["hotelId"]))
            places = rec["places"] + places
            db.hotel_pois.update(
                    {"hotelId": rec["hotelId"]},
                    {"$set": {"places": places}},
                    )
    except pymongo.errors.PyMongoError as e:
        logger.error("Failure %s" % (e.reason))
    if next_page_token:
        params = {
                "location": "%s,%s" % (
                    str(context["latitude"]), str(context["longitude"])),
                "pagetoken": next_page_token,
                }
        task = crawl_helper.FetchTask(
                config=config_places,
                context=context,
                params=params,
                process_response=handle_places_response,
                )
        fetcher_pool.queue.put(task)


def step_wait():
    while not fetcher_pool.queue.empty():
        time.sleep(0.1)
    logger.info("[X] Waiting to complete...")
    time.sleep(15)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(description=__doc__,
            version="%%prog v%s" % __version__)
    #parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
    # default=False, help="Increase verbosity")

    opts, args = parser.parse_args()

    types = {
            "airport": "airport",
            "banking": "atm|bank|finance",
            "entertainment": "bowling_alley|movie_theater|spa|stadium",
            "medical": "dentist|doctor|hospital|pharmacy|physiotherapist",
            "public transport": "bus_station|car_rental|subway_station|taxi_stand|train_station",
            "food": "bakery|bar|cafe|food|meal_delivery|meal_takeaway|restaurant",
            "shopping": "clothing_store|convenience_store|department_store|furniture_store|grocery_or_supermarket|home_goods_store|jewelry_store|shopping_mall",
            "tourist attraction": "amusement_park|aquarium|art_gallery|casino|museum|night_club|park|zoo",
            }


# 1. Find all places within 2 k radius for each hotel

    logger.info ("[X] Starting places search...")
    hotels = db.hotels.find()
    for h in hotels:
        if db.hotel_pois.find_one({"hotelId": h["hotelId"]}):
            continue
        if all (k in h for k in ("latitude", "longitude")):
            params = {
                    "location": "%s,%s" % (
                        str(h["latitude"]), str(h["longitude"]))
                    }
            context={
                    "hotelId": h["hotelId"],
                    "latitude": h["latitude"],
                    "longitude": h["longitude"],
                    }
            task = crawl_helper.FetchTask(
                    config=config_places,
                    context=context,
                    params=params,
                    process_response=handle_places_response,
                    )
            fetcher_pool.queue.put(task)

# 2. Wait till queue is drained

    step_wait()

# 3. Stop the pool

    logger.info("[X] Stopping fetcher pool")
    fetcher_pool.stop()
