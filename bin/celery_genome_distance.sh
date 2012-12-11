#!/bin/bash
celery -A genome.genome_distance worker --loglevel=debug -Q distance -n distance
