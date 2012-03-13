#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for storing or clearing data in whoosh indices.

Usage: python3 index.py <build|store|clear> [index]
Run 'python3 index.py build' to build all empty indices at once.
"""
import os
import sys
import time
import json
from math import log

from whoosh.index import create_in, open_dir, exists_in
from whoosh.analysis import StandardAnalyzer
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.qparser import QueryParser, OrGroup

from data import ATC, ICD, PatientCase, Therapy, populate_all, get_stopwords


# Folder to store whoosh index in
INDEX_DIR = 'whooshindex'


# Analyzer which removes stopwords
ANALYZER = StandardAnalyzer(stoplist=get_stopwords())


# Schema for storing and indexing ATC codes in whoosh database
ATC_SCHEMA = Schema(code=ID(stored=True), title=TEXT(stored=True))


# Schema for storing and indexing ICD10 codes in whoosh database
ICD_SCHEMA = Schema(code=ID(stored=True), short=ID(stored=True),
                    label=TEXT(stored=True), type=TEXT, icpc2_code=ID,
                    icpc2_label=TEXT, synonyms=TEXT, terms=TEXT,
                    inclusions=TEXT, exclusions=TEXT,
                    description=TEXT(analyzer=ANALYZER))


# Schema for storing and indexing PatientCase
CASE_SCHEMA = Schema(code=ID(stored=True, unique=True),
                     text=TEXT(vector=True, analyzer=ANALYZER))


# Schema for storing and indexing chapters in whoosh database
THERAPY_SCHEMA = Schema(code=ID(stored=True, unique=True),
                        title=TEXT(stored=True),
                        text=TEXT(vector=True, analyzer=ANALYZER))


# Map index name to schema
SCHEMA_MAP = {'atc': ATC_SCHEMA, 'icd': ICD_SCHEMA,
              'case': CASE_SCHEMA, 'therapy': THERAPY_SCHEMA}


def get_empty_indices():
    """Check if indices exists and contains documents."""
    classes = [ATC, ICD, PatientCase, Therapy]
    if os.path.isdir(INDEX_DIR):
        for i in reversed(range(len(classes))):
            if exists_in(INDEX_DIR, indexname=classes[i]._NAME):
                ix = open_dir(INDEX_DIR, indexname=classes[i]._NAME)
                if ix.doc_count() > 0:
                    classes.pop(i)
    return classes


def create_or_open_index(cls):
    """Create index if necessary, open otherwise."""
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    if not exists_in(INDEX_DIR, indexname=cls._NAME):
        ix = create_in(INDEX_DIR, SCHEMA_MAP[cls._NAME], cls._NAME)
        print("Created %s index '%s'" % (cls.__name__, cls._NAME))
    else:
        ix = open_dir(INDEX_DIR, cls._NAME)
    return ix


def store_objects_in_index(cls):
    """Store all cls objects in its index."""
    try:
        objects = cls.ALL.values()
    except AttributeError:
        objects = cls.ALL
    now = time.time()

    ix = create_or_open_index(cls)
    with ix.writer() as writer:
        for obj in objects:
            writer.add_document(**obj.to_index())

    print("Stored %s %s objects in index in %.2f seconds" % (
            len(objects), cls.__name__, time.time() - now))


def _idf(N, n):
    return log(N / n)  # Inverse frequency
def _idf_smooth(N, n):
    return log(1 + (N / n))  # Inverse frequency smooth
def _idf_prob(N, n):
    return log((N - n) / n)  # Probabilistic inverse frequency
def _tf_log_norm(frequency):
    return 1 + log(frequency)  # Log normalization


def create_vectors(tf=_tf_log_norm, idf=_idf):
    """Create vectors for PatientCase and Therapy objects."""
    c_ix = create_or_open_index(PatientCase)
    t_ix = create_or_open_index(Therapy)
    with c_ix.searcher() as c_searcher, t_ix.searcher() as t_searcher:

        # Inverse document frequency
        N = c_searcher.doc_count() + t_searcher.doc_count()
        def calc_idf(term):
            n = t_searcher.doc_frequency('text', term)
            n += c_searcher.doc_frequency('text', term)
            return idf(N, n)

        # Calcuate TF-IDF
        for cls, search in ((PatientCase, c_searcher), (Therapy, t_searcher)):
            now = time.time()
            for doc_num in search.document_numbers():
                obj = cls.ALL[search.stored_fields(doc_num)['code']]
                obj.vector = {t: tf(w) * calc_idf(t) for t, w in
                              search.vector_as('weight', doc_num, 'text')}

            # Dump to JSON
            with open(cls._JSON, 'w') as f:
                json.dump([i.to_json() for i in cls.ALL.values()], f, indent=4)
            print("Created %s vectors in %.2f seconds" % (
                    cls.__name__, time.time() - now))


def search(cls, field, query):
    """Perform a search on cls._NAME index on 'field' with 'query'."""
    ix = create_or_open_index(cls)
    qp = QueryParser(field, schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:
        q = qp.parse(query)
        objs = searcher.search(q)
        return [dict(i.items()) for i in searcher.search(q)]


def extract(fields, results, limit=10):
    """Extract specific values from each search result."""
    out = []
    for obj in results[:limit]:
        out.append(', '.join('%s: %s' % (key, obj[key]) for key in fields))
    return out


def print_result(result):
    """Simply print all results from a search."""
    print("Showing top %i results:" % len(result))
    for i, res in enumerate(result):
        print(i, res)


def main(script, command='', index='', field='', *query):
    """Store, clear or search data in whoosh indices.

    Can also be used to create vectors needed for task 3.
    'command' is either build|store|clean|search|vector
    'index' is either atc|icd|therapy|case

    Usage: python3 index.py <command> [index] [field] [query]
    """
    # Store all objects in index
    if command == 'build':
        populate_all()
        empty = get_empty_indices()
        for cls in empty:
            store_objects_in_index(cls)
        return

    classes = [ATC, ICD, PatientCase, Therapy]
    if index:
        classes = [i for i in classes if i._NAME == index]
        if not classes:
            print("Unknown index %s, valids: atc|icd|case|therapy" % index)
            sys.exit(2)

    # Store objects in index, will create duplicates if run several times
    if command == 'store':
        populate_all()
        for cls in classes:
            store_objects_in_index(cls)

    # Empty index
    elif command in ('clean', 'clear'):
        for cls in classes:
            create_or_open_index(cls)
            create_in(INDEX_DIR, SCHEMA_MAP[cls._NAME], cls._NAME)
            print("Emptied %s index" % cls.__name__)

    # Create vectors
    elif command.startswith('vector'):
        populate_all()
        create_vectors()

    # Search in whoosh index
    elif command == 'search':
        mapping = {'icd': ('short', 'label'), 'atc': ('code', 'title'),
                   'therapy': ('code', 'title'), 'case': ('code',)}
        query = ''.join(query)  # Flatten query
        cls, = classes  # Can only search on one index at a time
        print_result(extract(mapping[cls._NAME], search(cls, field, query)))

    # Unknown command
    else:
        print("Unknown command '%s'" % command)
        print("Usage: python3 index.py <command> [index] [field] [query]")
        print("Command is either build|store|clean|search|vector")
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
