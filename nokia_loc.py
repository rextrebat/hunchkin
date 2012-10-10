#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google Places - Get Nearby Places"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import pymongo
import time
import urlparse

import crawl_helper


logger = logging.getLogger('ean_hotel_desc')

# -- globals
conn = pymongo.Connection("localhost", 27017)
db = conn.hotelgenome

throttler1 = crawl_helper.Throttler(10, 1)

base_url = "http://demo.places.nlp.nokia.com/places/v1/discover/explore"

base_params = {
        "app_id": "txuyFL-drAd4lXn3WOjJ",
        "app_code": "s6nJMZIO26OHLeUA3BoDQA",
        "tf": "plain",
        }

config_places = crawl_helper.FetcherConfig(
        base_url=base_url,
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.JSON,
        headers=dict(
            Accept="application/json"),
        )

fetcher_pool = crawl_helper.FetcherPool(
        size=5,
        throttlers=[throttler1]
        )


def get_next_page_params(np_url, context):
    """
    Get the url parameters for the next page
    e.g. http://demo.places.nlp.nokia.com/places/v1/discover/explore;context=Zmxvdy1pZD04Y2Q3ZjE5Ny1jOWU2LTRmZDgtYjk4YS1iN2FiNTMzNGIxOWFfMTM0OTgzNzAzODE1MF8wXzIwMTI?app_id=demo_qCG24t50dHOwrLQ&app_code=NYKC67ShPhQwqaydGIW4yg&offset=10&at=37.7851%2C-122.4047&size=10
    """
    np_dict = urlparse.parse_qs(np_url)
    params = dict(
            context=np_dict['context'][0],
            offset=np_dict['offset'][0],
            size=np_dict['size'][0],
            )
    params_no_encode = "in=%s,%s;r=5000" % (
                    str(context["latitude"]), str(context["longitude"]))

    return (params, params_no_encode)


def handle_places_response(response, context):
    """
    handler - response to places search
    """
    if "next" in response["results"]:
        next_page = response["results"]["next"]
    else:
        next_page = None
    places = response["results"]["items"]
    response = {}
    response["hotelId"] = context["hotelId"]
    response["places"] = places
    try:
        rec = db.hotel_pois_nokia.find_one({"hotelId": response["hotelId"]})
        if not rec:
            logger.debug("inserting hotel id %s" % (response["hotelId"]))
            db.hotel_pois_nokia.insert(response)
        else:
            logger.debug("updating hotel id %s" % (response["hotelId"]))
            places = rec["places"] + places
            db.hotel_pois_nokia.update(
                    {"hotelId": rec["hotelId"]},
                    {"$set": {"places": places}},
                    )
    except pymongo.errors.PyMongoError as e:
        logger.error("Failure %s" % (e.reason))
    if next_page:
        params, params_no_encode = get_next_page_params(next_page, context)
        task = crawl_helper.FetchTask(
                config=config_places,
                context=context,
                params=params,
                params_no_encode=params_no_encode,
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


# 1. Find all places within 5 k radius for each hotel

    logger.info ("[X] Starting places search...")
    hotels = db.hotels.find()
    #hotels = db.hotels.find(
            #{"hotelId": {"$in": [228014,125813,188071,111189,212448]}}
            #)
    for h in hotels:
        if db.hotel_pois_nokia.find_one({"hotelId": h["hotelId"]}):
            continue
        if all (k in h for k in ("latitude", "longitude")):
            params_no_encode = "in=%s,%s;r=5000" % (
                        str(h["latitude"]), str(h["longitude"]))
            context={
                    "hotelId": h["hotelId"],
                    "latitude": h["latitude"],
                    "longitude": h["longitude"],
                    }
            task = crawl_helper.FetchTask(
                    config=config_places,
                    context=context,
                    params_no_encode=params_no_encode,
                    process_response=handle_places_response,
                    )
            fetcher_pool.queue.put(task)

# 2. Wait till queue is drained

    step_wait()

# 3. Stop the pool

    logger.info("[X] Stopping fetcher pool")
    fetcher_pool.stop()
