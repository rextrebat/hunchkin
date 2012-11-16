#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tag genes for hotels based on stored rules"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
from collections import namedtuple
from celery import Celery
import celery
import urllib2
import urllib
import json

from celery.signals import worker_init, task_prerun

# ---GLOBALS

logger = logging.getLogger("gene_tagger")

conn = None

hotels = None

celery = Celery('ean_tasks', backend="amqp", broker="amqp://")
avail_base_url = "http://api.ean.com/ean-services/rs/hotel/v3/list"


@celery.task
def get_avail_hotels(date_from, date_to, hotel_ids):
    """
    return hotels with availability
    """
    base_params = {
            "minorRev": 16,
            "apiKey": "5rrrsn5skrcjbhcpggvek38u",
            "cid": "55505",
            "customerUserAgent": "None",
            "customerIpAddress": "None",
            "locale": "en_US",
            "currencyCode": "USD"
            }
    params = {}
    params["arrivalDate"] = date_from
    params["departureDate"] = date_to
    params["hotelIdList"] = ",".join([str(h_id) for h_id in hotel_ids])
    url = avail_base_url + "?" + urllib.urlencode(base_params) + \
            urllib.urlencode(params)
    try:
        logger.debug("Request: \n %s" % (str(url)[:1024]))
        request = urllib2.Request(
                url=url,
                headers={}
                )
        response = urllib2.urlopen(request).read()
        logger.debug("Response: \n %s" % (str(response)[:1024]))
    except urllib2.URLError as e:
        logger.error("Failure %s" % (e.reason))
    avail_hotels = {}
    response = json.loads(response)
    hotel_list = response.get(
            "HotelListResponse", {}).get(
                    "HotelList", {}).get(
                            "HotelSummary",[])
    if type(hotel_list) != list:
        hotel_list = [hotel_list]
    while response.get("HotelListResponse", {}).get(
            "moreResultsAvailable"):
        params = {}
        params["cacheKey"] = response.get(
                "HotelListResponse", {}).get(
                        "cacheKey", "")
        params["cacheLocation"] = response.get(
                "HotelListResponse", {}).get(
                        "cacheLocation", "")
        params["customerSessionId"] = response.get(
                "HotelListResponse", {}).get(
                        "customerSessionId", "")
        url = avail_base_url + "?" + urllib.urlencode(base_params) + \
                urllib.urlencode(params)
        try:
            logger.debug("Request: \n %s" % (str(url)[:1024]))
            request = urllib2.Request(
                    url=url,
                    headers={}
                    )
            response = urllib2.urlopen(request).read()
            logger.debug("Response: \n %s" % (str(response)[:1024]))
        except urllib2.URLError as e:
            logger.error("Failure %s" % (e.reason))
        response = json.loads(response)
        more_hotel_list = response.get(
                "HotelListResponse", {}).get(
                        "HotelList", {}).get(
                                "HotelSummary",[])
        if type(more_hotel_list) != list:
            more_hotel_list = [more_hotel_list]
        hotel_list += more_hotel_list
    for h in hotel_list:
        low_rate = int(round(h["lowRate"]))
        high_rate = int(round(h["highRate"]))
        avail_hotels[h["hotelId"]] = dict(
                low_rate=low_rate,
                high_rate=high_rate,
                available=True,
                )
    for h_id in hotel_ids:
        if h_id not in avail_hotels:
            avail_hotels[h_id] = dict(
                    available=False
                    )
    return avail_hotels


@worker_init.connect
def initialize_crawler(sender=None, conf=None, **kwargs):
    pass


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

    logger.info("[X] Checking aviability")
    hotel_ids = [228014,125813,188071,111189,212448]
    print get_avail_hotels(
            date_from="12/01/2012",
            date_to="12/05/2012",
            hotel_ids=hotel_ids,
            )

    logger.info("[X] Done")


