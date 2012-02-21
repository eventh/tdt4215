#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for searching in the whoosh database.
"""
import sys

from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from schemas import ICD10_SCHEMA, INDEX_DIR


def search_icd10(query, result_func=None):
    """Search the ICD10 index with 'query'."""
    ix = open_dir(INDEX_DIR, indexname='icd10')
    with ix.searcher() as searcher:

        # Search
        qp = QueryParser('label', schema=ix.schema)
        q = qp.parse(query)
        result = searcher.search(q)

        # Handle result
        if result_func is None:
            result_func = print_result
        result_func(result)


def print_result(result):
    """Simply print all results from a search."""
    print result
    for res in result:
        print res


def main(script, index='', *query):
    """Perform a search on our whoosh database.

    Usage: python search.py <index> <query>
    Example: 'python search.py icd10 Kolera'
    'index' is one of icd10 or ...
    """
    flat_query = unicode(''.join(query))  # TODO

    if index == 'icd10':
        search_icd10(flat_query)

    else:
        print "Unknown database: %s" % index
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
