#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery import Celery
from config.celeryconfig import CeleryConfig


celery = Celery("bin.celeryapp",
        backend="amqp",
        broker="pyamqp://",
        include=["genome.chromosome_distance", "avail.ean_tasks"])
celery.config_from_object(CeleryConfig)
