#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Get Hotels for a given destination"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

import pymongo
import json
import urllib2
import urllib


logger = logging.getLogger('get_hotels_for_dest')

# -- globals
conn = pymongo.Connection("localhost", 27017)
db = conn.accures

base_url = "http://api.ean.com/ean-services/rs/hotel/v3/list?"
base_url += "cid=55505"
base_url += "&apiKey=5rrrsn5skrcjbhcpggvek38u"
base_url += "&minorRev=16"
base_url += "&customerUserAgent=None"
base_url += "&customerIpAddress=None"
base_url += "&locale=en_US"
base_url += "&currencyCode=USD"


def get_json_response(url):
    logger.debug("Fetching...%s" % (url))
    response = json.loads(urllib2.urlopen(url).read())
    # logger.debug("Retrieved:\n %s" % str(response))
    return response


def get_hotel_desc(hotelid):
    pass


def get_hotels_for_destination(dest):
    url = base_url + "&" + urllib.urlencode({
            "destinationString": dest,
            "supplierCacheTolerance": "MED_ENHANCED",
            })
    response = get_json_response(url)
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


