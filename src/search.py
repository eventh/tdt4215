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


def search(cls, field, query):
    """Perform a search on cls.NAME index on 'field' with 'query'."""
    ix = open_dir(INDEX_DIR, indexname=cls.NAME)
    qp = QueryParser(field, schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:
        q = qp.parse(query)
        objs = searcher.search(q)
        return [dict(i.items()) for i in searcher.search(q)]


def extract(fields, results, limit=10):
    """Extract specific values from each result."""
    out = []
    for obj in results[:limit]:
        out.append(', '.join('%s: %s' % (key, obj[key]) for key in fields))
    return out


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

    query = ''.join(query)  # Flatten query

    if index == 'icd':
        res = extract(('short', 'label'), search(ICD10, field, query))
    elif index == 'atc':
        res = extract(('code', 'name'), search(ATC, field, query))
    elif index == 'terapi':
        res = extract(('code', 'title'), search(Chapter, field, query))
    else:
        print("Unknown database: %s" % index)
        sys.exit(2)

    print_result(res)
    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
