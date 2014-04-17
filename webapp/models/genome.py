#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genome model
"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

from webapp.extensions import db

class GenomeRule(db.Model):

    __tablename__ = "genome_rules"

    category = db.Column(db.String(64))
    sub_category = db.Column(db.String(64))
    gene_name = db.Column(db.String(128))
    gene_code = db.Column(db.String(128))
    bitmask = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.String(64))
    parameters = db.Column(db.String(256))
    chromosome = db.Column(db.String(64))
    gene_usage = db.Column(db.String(32))
    weight = db.Column(db.Integer)
    gene_source = db.Column(db.String(64))


class GenomeCategory(db.Model):

    __tablename__ = "genome_categories"

    chromosome_id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64))
    sub_category = db.Column(db.String(64))
    chromosome = db.Column(db.String(64))
    measure_type = db.Column(db.String(32))
    category_order = db.Column(db.Integer)
    normalization_method = db.Column(db.String(32))
    normalization_factor = db.Column(db.Integer)


