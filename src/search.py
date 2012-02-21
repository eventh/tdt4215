#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for searching in the whoosh database.
"""
import sys

from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from schemas import ICD10_SCHEMA, INDEX_DIR


def search_icd10(query):
    ix = open_dir(INDEX_DIR, indexname='icd10')
    with ix.searcher() as searcher:
        qp = QueryParser('label', schema=ix.schema)
        q = qp.parse(u'test')
        result = searcher.search(q)
    return result


def main(script, index='', *query):
    if index == 'icd10':
        results = search_icd10(query)

    else:
        print "Unknown database: %s" % index
        sys.exit(2)

    # Print results
    print results


if __name__ == '__main__':
    main(*sys.argv)
