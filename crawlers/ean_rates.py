#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EAN - Cache hotel rates"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging

import MySQLdb
import time
from datetime import date, timedelta



logger = logging.getLogger('ean_hotel_desc')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('../out/ean_rates.out')
file_formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(stream_formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

crawl_logger = logging.getLogger('crawl_helper')
crawl_logger.addHandler(file_handler)
crawl_logger.addHandler(stream_handler)

import crawl_helper

# -- globals
conn = None

days_ahead = [5, 10, 20, 30, 60]
batch_size = 50

throttler1 = crawl_helper.Throttler(5, 1)
throttler2 = crawl_helper.Throttler(490, 3600)

base_url = "http://api.ean.com/ean-services/rs/hotel/v3/"

base_params = {
        "cid": "55505",
        "apiKey": "5rrrsn5skrcjbhcpggvek38u",
        "minorRev": "16",
        "customerUserAgent": "None",
        "customerIpAddress": "None",
        "locale": "en_US",
        "currencyCode": "USD",
        "supplierCacheTolerance": "MAX_ENHANCED",
        }

config_list = crawl_helper.FetcherConfig(
        base_url=base_url + "list",
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.JSON
        )

fetcher_pool = crawl_helper.FetcherPool(
        size=5,
        throttlers=[throttler1, throttler2]
        )


def handle_hotel_list(response, context):
    """
    handler for hotel list
    """
    hotel_list = response.get(
            "HotelListResponse", {}).get(
                    "HotelList", {}).get(
                            "HotelSummary",[])
    if type(hotel_list) != list:
        hotel_list = [hotel_list]
    #cursor = conn.cursor()
    for h in hotel_list:
        hotel_id = h["hotelId"]
        low_rate = round(h["lowRate"], 2)
        high_rate = round(h["highRate"], 2)
        TA_rating_url = h.get("tripAdvisorRatingUrl","")
        logger.info(
                "Hotel Id: %d, Date: %s, Rates: %f - %f" % (
                    hotel_id,
                    context["arrivalDate"],
                    low_rate,
                    high_rate)) 
        logger.info(
                "Hotel Id: %d, Trip Advisor URL: %s" % \
                        (hotel_id, TA_rating_url))
        #cursor.execute(
                #"""
                #INSERT INTO hotel_rates
                #(hotel_id, arrival_date, departure_date, low_rate, high_rate)
                #VALUES
                #(%s, STR_TO_DATE(%s,'%%m/%%d/%%Y'),
                #STR_TO_DATE(%s, '%%m/%%d/%%Y'), %s, %s)
                #""",(
                #hotel_id,
                #context['arrivalDate'],
                #context['departureDate'],
                #low_rate,
                #high_rate
                #))
        #cursor.execute(
                #"""
                #INSERT INTO hotel_attrs
                #(hotel_id, trip_advisor_rating_url)
                #VALUES
                #(%s, %s)
                #ON DUPLICATE KEY UPDATE
                #trip_advisor_rating_url = %s
                #""",
                #(hotel_id, TA_rating_url, TA_rating_url)
                #)
    #conn.commit()
    if response.get("HotelListResponse", {}).get(
            "moreResultsAvailable"):
        enqueue_followon_request(response, context)


def step_wait():
    while not fetcher_pool.queue.empty():
        time.sleep(0.1)
    logger.info("[X] Waiting to complete...")
    time.sleep(15)


def enqueue_request(hotel_ids, date_from, date_to):
    """
    enqueue a single request; dates passed as strings
    """
    params = {
            "hotelIdList": ",".join(
                [str(h) for h in hotel_ids]),
            "arrivalDate": date_from,
            "departureDate": date_to,
            }
    context = {
            "arrivalDate": date_from,
            "departureDate": date_to,
            }
    task = crawl_helper.FetchTask(
            config=config_list,
            context=context,
            params=params,
            process_response=handle_hotel_list,
            )
    fetcher_pool.queue.put(task)


def enqueue_followon_request(response, context):
    """
    enqueue a request when "moreResultsAvailable" is in response
    """
    params = {}
    params["cachekey"] = response.get(
            "HotelListResponse", {}).get(
                    "cacheKey", "")
    params["cachelocation"] = response.get(
            "HotelListResponse", {}).get(
                    "cacheLocation", "")
    params["customersessionid"] = response.get(
            "HotelListResponse", {}).get(
                    "customerSessionId", "")
    task = crawl_helper.FetchTask(
            config=config_list,
            context=context,
            params=params,
            process_response=handle_hotel_list,
            )
    fetcher_pool.queue.put(task)


def enqueue_all(hotel_ids):
    """
    enqueue all requests
    """
    hotel_batches = [hotel_ids[i:i+batch_size] for i in range(
        0, len(hotel_ids), batch_size)]
    today = date.today()
    date_batches = [
            (today + timedelta(d), today + timedelta(d+1)) \
                    for d in days_ahead]
    for date_from, date_to in date_batches:
        for hotel_batch in hotel_batches:
            enqueue_request(
                    hotel_batch,
                    date_from.strftime("%m/%d/%Y"),
                    date_to.strftime("%m/%d/%Y"),
                    )


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(description=__doc__,
            version="%%prog v%s" % __version__)
    #parser.add_option('-v', '--verbose', action="store_true", dest="verbose",
    # default=False, help="Increase verbosity")

    opts, args = parser.parse_args()

    conn = MySQLdb.Connection(
            host="localhost",
            user="appuser",
            passwd="rextrebat",
            db="hotel_genome"
            )


# 1. Fetch hotels and then descriptions for the hotels

    logger.info ("[X] Fetching hotel list from db...")
    cursor = conn.cursor()
    cursor.execute(
            """
            SELECT EANHotelID FROM EAN_ActiveProperties
            """
            )
    rows = cursor.fetchall()
    hotel_ids = [h for hl in rows for h in hl]
    #hotel_ids = [228014,125813,188071,111189,212448]

# 2. Enqueue All
    logger.info ("[X] Getting Rates...")
    enqueue_all(hotel_ids)

# 3. Wait till queue is drained

    step_wait()

# 4. Stop the pool

    logger.info("[X] Stopping fetcher pool")
    fetcher_pool.stop()
