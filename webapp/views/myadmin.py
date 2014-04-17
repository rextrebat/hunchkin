#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""genome admin view"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"


from flask.ext.admin.contrib.sqla import ModelView
from webapp.models import GenomeRule

class GenomeRuleView(ModelView):

    can_create = False

    column_list = ('bitmask', 'category', 'sub_category', 'gene_name', 'gene_code', 
            'function', 'parameters', 'chromosome', 
            'gene_usage', 'weight', 'gene_source')

    page_size = 600

    def __init__(self, session, **kwargs):
        super(GenomeRuleView, self).__init__(GenomeRule, session, **kwargs)

