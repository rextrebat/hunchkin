#!/bin/bash
celery -A avail.ean_tasks worker --loglevel=debug -Q avail -n avail --concurrency=1
