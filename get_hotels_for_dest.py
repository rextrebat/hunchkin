#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get Hotels for a given destination"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import pymongo

import crawl_helper




logger = logging.getLogger('get_hotels_for_dest')

# -- globals
conn = pymongo.Connection("localhost", 27017)
db = conn.accures

throttler = crawl_helper.Throttler(5, 1)

base_url = "http://api.ean.com/ean-services/rs/hotel/v3/list"

base_params = {
        "cid": "55505",
        "apiKey": "5rrrsn5skrcjbhcpggvek38u",
        "minorRev": "16",
        "customerUserAgent": "None",
        "customerIpAddress": "None",
        "locale": "en_US",
        "currencyCode": "USD"
        }

requester = crawl_helper.HTTPRequester(
        base_url=base_url,
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.JSON,
        throttler=throttler
        )


def get_hotel_desc(hotelid):
    pass


def get_hotels_for_destination(dest):
    params = {
            "destinationString": dest,
            "supplierCacheTolerance": "MED_ENHANCED",
            }
    response = requester.get(params)
    logger.info("Retrieved...%s properties" % (
        str(response["HotelListResponse"]["HotelList"][
            "@activePropertyCount"])))


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

    for d in dests:
        get_hotels_for_destination(d)


