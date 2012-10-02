#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Latent Semantic Analysis"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import logging
import re
import nltk
from numpy import zeros
from scipy.linalg import svd
from math import log
from numpy import asarray, sum

# ---GLOBALS

logger = logging.getLogger("lsa")

ignore = re.compile(r"""['&-.?!,":;()|0-9]""")
stopwords = nltk.corpus.stopwords.words('english')

class LSA(object):
    def __init__(self, stopwords=stopwords, ignore=ignore):
        self.stopwords = stopwords
        self.ignore = ignore
        self.wdict = {}
        self.dcount = 0
        self.hist = None

    def parse(self, doc):
        raw = nltk.clean_html(doc)
        text = nltk.Text(nltk.word_tokenize(raw))
        words = [w.lower() for w in text]
        for w in words:
            if self.ignore.search(w):
                continue
            elif w in self.stopwords:
                continue
            elif w in self.wdict:
                self.wdict[w].append(self.dcount)
            else:
                self.wdict[w] = [self.dcount]
        self.dcount += 1


    def histogram(self):
        self.hist = [(k, len(self.wdict[k])) for k in self.wdict.keys()]
        self.hist.sort(key=lambda w:w[1], reverse=True)


    def build(self):
        self.keys = [k for k in self.wdict.keys() if len(self.wdict[k]) > 1]
        self.keys.sort()
        self.A = zeros([len(self.keys), self.dcount])
        for i, k in enumerate(self.keys):
            for d in self.wdict[k]:
                self.A[i,d] += 1


    def calc(self):
        self.U, self.S, self.Vt = svd(self.A)


    def TFIDF(self):
        WordsPerDoc = sum(self.A, axis=0)
        DocsPerWord = sum(asarray(self.A > 0, 'i'), axis=1)
        rows, cols = self.A.shape
        for i in range(rows):
            for j in range(cols):
                self.A[i,j] = (self.A[i,j] / WordsPerDoc[j]) * log(float(cols) / DocsPerWord[i])


    def printA(self):
        print 'Here is the count matrix'
        print self.A


    def printSVD(self):
        print 'Here are the singular values'
        print self.S
        print 'Here are the first 3 columns of the U matrix'
        print -1*self.U[:, 0:3]
        print 'Here are the first 3 rows of the Vt matrix'
        print -1*self.Vt[0:3, :]

