#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google search for Trip Advisor base URL"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

import pymongo
import time
import urlparse

import crawl_helper


logger = logging.getLogger('tripadvisor_reviews')

# -- globals
conn = pymongo.Connection("localhost", 27017)
db = conn.hotelgenome

throttler1 = crawl_helper.Throttler(5, 1)

base_url = "http://www.google.com/"

base_params = {
        }

config_search = crawl_helper.FetcherConfig(
        base_url=base_url,
        base_params=base_params,
        response_format=crawl_helper.ResponseFormat.SOUP
        )

fetcher_pool = crawl_helper.FetcherPool(
        size=5,
        throttlers=[throttler1]
        )


def handle_hotel_search(response, context):
    """
    handler for hotel list
    """
    search_results = response.find(id="search")
    items = search_results.findAll("li", {"class": "g"})
    for i in items:
        link = i.div.h3.a
        if link:
            href = link["href"]
            params = urlparse.parse_qs(href)
            url = params["url"]
            if "Hotel_Review" in url:
                review_link = url
    if review_link:
        hotel_id = context["hotel_id"]
        db.ta_review_links.save({
            "hotel_id": hotel_id,
            "review_link": review_link,
            })
        logger.info(
                "[.]Search successful for hotel %d" % context["hotel_id"])
        return
    else:
        logger.error(
                "[.]Search failed for hotel %d" % context["hotel_id"])
        return


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

    import MySQLdb

    def remove_non_ascii(s):
        return "".join(i for i in s if ord(i)<128)

# 1.Fetch hotels from EAN_ActiveProperties and get links

    logger.info ("[X] Fetch hotel review links...")
    dbconn = MySQLdb.Connection(
        host="localhost",
        user="appuser",
        passwd="rextrebat",
        db="hotel_genome"
        )
    cursor = dbconn.cursor()
    cursor.execute(
            """
            SELECT EANHotelID, Name, City, CountryName
            FROM EAN_ActiveProperties p, EAN_CountryList c
            WHERE p.Country = c.CountryCode
            AND mod(EANHotelID, 10000) = 1;
            """
            )
    rows = cursor.fetchall()
    logger.info ("[X] Searching %d hotels" % len(rows))
    for r in rows:
        hotel_id, name, city, country = r
        name = remove_non_ascii(name)
        context = {
                'hotel_id': hotel_id,
                'hotel_name': name,
                }
        search_param = name + " " + city + " " + country
        search_param += " site:tripadvisor.com"
        params = {
                "q": search_param,
                }
        task = crawl_helper.FetchTask(
                config=config_search,
                context=context,
                params=params,
                process_response=handle_hotel_search,
                )
        fetcher_pool.queue.put(task)
    cursor.close()

# 2. Wait till queue is drained

    step_wait()

# 3. Stop the pool

    logger.info("[X] Stopping fetcher pool")
    fetcher_pool.stop()
