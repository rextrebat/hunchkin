#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EAN - Get Hotels for a given destination"""

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

throttler1 = crawl_helper.Throttler(5, 1)
throttler2 = crawl_helper.Throttler(400, 3600)

base_url = "http://api.ean.com/ean-services/rs/hotel/v3/"

base_params = {
        "cid": "55505",
        "apiKey": "5rrrsn5skrcjbhcpggvek38u",
        "minorRev": "16",
        "customerUserAgent": "None",
        "customerIpAddress": "None",
        "locale": "en_US",
        "currencyCode": "USD"
        }

config_list = crawl_helper.FetcherConfig(
        base_url=base_url + "list",
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.JSON
        )

config_info = crawl_helper.FetcherConfig(
        base_url=base_url + "info",
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.JSON
        )

fetcher_pool = crawl_helper.FetcherPool(
        size=5,
        throttlers=[throttler1, throttler2]
        )


def handle_hotel_list(response):
    """
    handler for hotel list
    """
    hotels = response["HotelListResponse"]["HotelList"]["HotelSummary"]
    for h in hotels:
        try:
            if not db.hotels.find_one({"hotelId":h["hotelId"]}):
                logger.debug("inserting hotel id %s" % (h["hotelId"]))
                db.hotels.insert(h)
        except pymongo.errors.PyMongoError as e:
            logger.error("Failure %s" % (e.reason))

def handle_hotel_desc(response):
    """
    handler for hotel desc
    """
    desc = response["HotelInformationResponse"]
    try:
        if not db.hotel_descs.find_one({"@hotelId":desc["@hotelId"]}):
            logger.debug("inserting desc for hotel id %s" % (
                desc["@hotelId"]))
            db.hotel_descs.insert(desc)
    except pymongo.errors.PyMongoError as e:
        logger.error("Failure %s" % (e.reason))

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

    dests = [
            "Negril, Jamaica",
            "Honolulu, Hawaii",
            "Phuket, Thailand",
            "San Diego, California",
            "Goa, India",
            ]

# 1. Fetch hotels and then descriptions for the hotels

    logger.info ("[X] Starting fetch hotels...")
    for d in dests:
        params = {
                "destinationString": d,
                "supplierCacheTolerance": "MED_ENHANCED",
                }
        task = crawl_helper.FetchTask(
                config=config_list,
                params=params,
                process_response=handle_hotel_list,
                )
        fetcher_pool.queue.put(task)

# 2. Wait till queue is drained

    step_wait()

# 3. Fetch descriptions
    logger.info ("[X] Starting fetch descriptions...")
    hotels = db.hotels.find({}, {"hotelId":1})
    for h in hotels:
        try:
            if db.hotel_descs.find_one({"@hotelId":str(h["hotelId"])}):
                continue
        except pymongo.errors.PyMongoError as e:
            logger.error("Failure %s" % (e.reason))
        params = {
                "hotelId": str(h["hotelId"]),
                "options": "0",
                }
        task = crawl_helper.FetchTask(
                config=config_info,
                params=params,
                process_response=handle_hotel_desc,
                )
        fetcher_pool.queue.put(task)


# 4. Wait till queue is drained

    step_wait()

# 4. Stop the pool

    logger.info("[X] Stopping fetcher pool")
    fetcher_pool.stop()
