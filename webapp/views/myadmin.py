#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""genome admin view"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"


from flask.ext.admin.contrib.sqla import ModelView
from webapp.models import GenomeRule, GenomeCategory

class GenomeRuleView(ModelView):


    column_list = (
            'gr_id',
            'bitmask',
            'category', 
            'sub_category',
            'gene_name',
            'gene_code', 
            'function',
            'parameters',
            'chromosome',
            'chromosome_id',
            'gene_usage',
            'weight',
            'gene_source'
            )

    page_size = 600

    def __init__(self, session, **kwargs):
        super(GenomeRuleView, self).__init__(GenomeRule, session, **kwargs)


class GenomeCategoryView(ModelView):


    column_list = (
            'chromosome_id',
            'category',
            'sub_category',
            'chromosome',
            'measure_type',
            'category_order',
            'normalization_method',
            'normalization_factor'
            )

    page_size = 600

    def __init__(self, session, **kwargs):
        super(GenomeCategoryView, self).__init__(GenomeCategory, session, **kwargs)
