#!/bin/bash

celeryd -A bin.celeryapp -l debug --pidfile=/var/log/hunchkin/celery.pid
