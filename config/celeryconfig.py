#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Celery Config"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

class CeleryConfig:
    CELERY_ENABLE_UTC = True
    CELERY_ROUTES = {
            'genome.genome_distance': {'queue': 'distance'},
            'genome.chromosome_distance': {'queue': 'distance'},
            'avail.ean_tasks': {'queue': 'avail'},
            }
