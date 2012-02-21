#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for searching in the whoosh database.
"""
import sys

from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from schemas import ICD10_SCHEMA, INDEX_DIR


def print_result(result):
    print result
    for res in result:
        print res


def search_icd10(query):
    ix = open_dir(INDEX_DIR, indexname='icd10')
    with ix.searcher() as searcher:
        qp = QueryParser('label', schema=ix.schema)
        q = qp.parse(query)
        print_result(searcher.search(q))


def main(script, index='', *query):
    flat_query = unicode(''.join(query))  # TODO

    if index == 'icd10':
        search_icd10(flat_query)

    else:
        print "Unknown database: %s" % index
        sys.exit(2)


if __name__ == '__main__':
    main(*sys.argv)
