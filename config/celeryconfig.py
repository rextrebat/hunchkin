#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Celery Config"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

from kombu import Queue

class CeleryConfig:
    CELERY_ENABLE_UTC = True
    CELERY_QUEUES = (
            Queue('distance', routing_key="genome.chromosome_distance"),
            Queue('avail', routing_key="avail.ean_tasks")
            )
    CELERY_ROUTES = {
            'genome.genome_distance': {'queue': 'distance'},
            'genome.chromosome_distance': {'queue': 'distance'},
            'avail.ean_tasks': {'queue': 'avail'},
            }
    CELERYD_PID_FILE="/var/log/hunchkin/%n.pid"
    CELERYD_CONCURRENCY=2

env_config = {}

env_config['DEV'] = {
        'db_host': 'localhost',
        'db_user': 'appuser',
        'db_passwd': 'rextrebat',
        'db_db': 'hotel_genome',
        }

env_config['PROD'] = {
        'db_host': 'localhost',
        'db_user': 'appuser',
        'db_passwd': 'rextrebat',
        'db_db': 'hotel_genome',
        }
