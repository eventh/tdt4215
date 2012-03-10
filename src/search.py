#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for searching in the whoosh database.
"""
import sys

from whoosh.qparser import QueryParser, OrGroup

from data import ATC, ICD, Therapy, PatientCase
from index import create_or_open_index


def search(cls, field, query):
    """Perform a search on cls._NAME index on 'field' with 'query'."""
    ix = create_or_open_index(cls)
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
    Example: 'python3 search.py icd label Kolera'
    'index' is one of icd, atc, case or therapy
    """
    if not query:
        print("Usage: python3 search.py <index> <field> <query>")
        sys.exit(2)

    query = ''.join(query)  # Flatten query

    if index == 'icd':
        res = extract(('short', 'label'), search(ICD, field, query))
    elif index == 'atc':
        res = extract(('code', 'title'), search(ATC, field, query))
    elif index == 'therapy':
        res = extract(('code', 'title'), search(Therapy, field, query))
    elif index == 'case':
        res = extract(('code', 'text'), search(PatientCase, field, query))
    else:
        print("Unknown database: %s" % index)
        sys.exit(2)

    print_result(res)
    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
