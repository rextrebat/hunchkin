#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

logger = logging.getLogger("social")

import MySQLdb
from flask import request, g, render_template, Blueprint, current_app
import simplejson as json
import uuid
import requests

social = Blueprint('social', __name__)

class Survey():

    def __init__(
            self,
            survey_id=None,
            region_id=None,
            created_by_id=None,
            created_by_first_name=None,
            created_by_last_name=None,
            created_by_name=None,
            hotel_ids=None):
        self.survey_id = survey_id
        self.region_id = region_id
        self.created_by_id = created_by_id
        self.created_by_first_name = created_by_first_name
        self.created_by_last_name = created_by_last_name
        self.created_by_name = created_by_name
        self.hotel_ids = hotel_ids
#hotels are tuples of (hotel_id, hotel_name)
        self.hotels = []
        self.region_name = None

    def fetch(self, s_id):
        cursor = g.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(
                """
                SELECT region_id, hotel_ids, created_by_id,
                created_by_first_name, created_by_last_name,
                created_by_name
                FROM survey WHERE survey_id = %s
                """, s_id)
        r = cursor.fetchone()
        self.survey_id = s_id
        self.region_id = r['region_id']
        self.created_by_id = r['created_by_id']
        self.created_by_first_name = r['created_by_first_name']
        self.created_by_last_name = r['created_by_last_name']
        self.created_by_name = r['created_by_name']
        self.fetch_region_name()
        self.hotel_ids = [int(h_id) for h_id in r['hotel_ids'].split(",")]
        self.fetch_hotel_names(r['hotel_ids'])

    def fetch_region_name(self):
        cursor = g.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(
                """
                SELECT RegionName
                FROM EAN_Regions
                WHERE RegionID = %s
                """, self.region_id)
        r = cursor.fetchone()
        self.region_name = r['RegionName']

    def fetch_hotel_names(self, ids):
        cursor = g.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(
                """
                SELECT EANHotelID, Name
                FROM EAN_ActiveProperties
                WHERE EANHotelID IN (%s)
                """ % (ids))
        rows = cursor.fetchall()
        self.hotels = [(int(r['EANHotelID']), r['Name']) for r in rows]

    def save(self):
        cursor = g.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute(
                """
                INSERT INTO survey
                (survey_id, region_id, hotel_ids,
                created_by_id, created_by_first_name,
                created_by_last_name, created_by_name)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.survey_id,
                    str(self.region_id),
                    ','.join([str(h) for h in self.hotel_ids]),
                    str(self.created_by_id),
                    self.created_by_first_name,
                    self.created_by_last_name,
                    self.created_by_name
                    )
                )
        g.db.commit()


@social.route('/social/save-survey', methods=['GET', 'POST'])
def save_survey():
    survey_id = str(uuid.uuid1())
    if request.method == "POST":
        data = json.loads(request.data)
    else:
        data = request.args
    region_id = data.get("region_id")
    hotel_ids = data.get("hotel_ids").split(",")
    created_by_id = int(data.get("created_by_id"))
    created_by_first_name = data.get("created_by_first_name")
    created_by_last_name = data.get("created_by_last_name")
    created_by_name = data.get("created_by_name")
    survey = Survey(
            survey_id=survey_id,
            region_id=region_id,
            hotel_ids=hotel_ids,
            created_by_id=created_by_id,
            created_by_first_name=created_by_first_name,
            created_by_last_name=created_by_last_name,
            created_by_name=created_by_name,
            )
    survey.save()
    return json.dumps(survey_id)


@social.route('/social/survey')
def view_survey():
    survey_id = request.args.get("survey_id")
    survey = Survey()
    survey.fetch(survey_id)
    return render_template(
            "survey.html",
            survey_id=survey_id,
            region_name=survey.region_name,
            created_by_id=survey.created_by_id,
            created_by_first_name=survey.created_by_first_name,
            created_by_last_name=survey.created_by_last_name,
            created_by_name=survey.created_by_name,
            hotels=survey.hotels
            )

