#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User Data Model
copied from fbone template
"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

from sqlalchemy.types import TypeDecorator, Text
from sqlalchemy.ext.mutable import Mutable


class DenormalizedText(Mutable, TypeDecorator):
    """
Stores denormalized primary keys that can be
accessed as a set.

:param coerce: coercion function that ensures correct
type is returned

:param separator: separator character
"""

    impl = Text

    def __init__(self, coerce=int, separator=" ", **kwargs):

        self.coerce = coerce
        self.separator = separator

        super(DenormalizedText, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None:
            items = [str(item).strip() for item in value]
            value = self.separator.join(item for item in items if item)
        return value

    def process_result_value(self, value, dialect):
         if not value:
            return set()
         return set(self.coerce(item) for item in value.split(self.separator))

    def copy_value(self, value):
        return set(value)
