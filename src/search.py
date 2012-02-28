#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for searching in the whoosh database.
"""
import sys

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from codes import ATC, ICD10, INDEX_DIR
from nlh import Chapter


def search_icd10(field, query):
    """Search the ICD10 index with 'query'."""
    ix = open_dir(INDEX_DIR, indexname=ICD10.NAME)
    qp = QueryParser(field, schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:
        q = qp.parse(query)
        objs = searcher.search(q)
        return ['%s: %s' % (i['short'], i['label']) for i in objs[:5]]


def search_atc(field, query):
    """Search the ATC index with 'query'."""
    ix = open_dir(INDEX_DIR, indexname=ATC.NAME)
    qp = QueryParser(field, schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:
        q = qp.parse(query)
        objs = searcher.search(q)
        return ['%s: %s' % (i['code'], i['name']) for i in objs[:5]]


def search_terapi(field, query):
    """Search the terapi chapter index with 'query'."""
    ix = open_dir(INDEX_DIR, indexname=Chapter.NAME)
    qp = QueryParser(field, schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:
        q = qp.parse(query)
        objs = searcher.search(q)
        return ['%s: %s' % (i['code'], i['title']) for i in objs[:5]]


def print_result(result):
    """Simply print all results from a search."""
    print("Showing top %i results:" % len(result))
    for i, res in enumerate(result):
        print(i, res)


def main(script, index='', field='', *query):
    """Perform a search on our whoosh database.

    Usage: python3 search.py <index> <field> <query>
    Example: 'python3 search.py icd10 label Kolera'
    'index' is one of icd, atc or terapi
    """
    if not query:
        print("Usage: python3 search.py <index> <field> <query>")
        sys.exit(2)

    flat_query = ''.join(query)

    if index == 'icd':
        print_result(search_icd10(field, flat_query))

    elif index == 'atc':
        print_result(search_atc(field, flat_query))

    elif index == 'terapi':
        print_result(search_terapi(field, flat_query))

    else:
        print("Unknown database: %s" % index)
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
