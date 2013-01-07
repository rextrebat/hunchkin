#!/bin/bash
celery -A genome.chromosome_distance worker --loglevel=debug -Q distance -n distance --concurrency=1
