#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import os
import sys
import time

from whoosh.index import create_in, open_dir, exists_in
from whoosh.analysis import StandardAnalyzer
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED

from data import ATC, ICD, Medicin, Therapy, populate_all, get_stopwords


INDEX_DIR = 'whooshindex'


ANALYZER = StandardAnalyzer(stoplist=get_stopwords())


# Schema for storing and indexing ATC codes in whoosh database
ATC_SCHEMA = Schema(code=ID(stored=True), title=TEXT(stored=True))


# Schema for storing and indexing ICD10 codes in whoosh database
ICD_SCHEMA = Schema(code=ID(stored=True), short=ID(stored=True),
                    label=TEXT(stored=True), type=TEXT, icpc2_code=ID,
                    icpc2_label=TEXT, synonyms=TEXT, terms=TEXT,
                    inclusions=TEXT, exclusions=TEXT, description=TEXT)


# Schema for storing and indexing Therapy chapters and PatientCase's
MEDIC_SCHEMA = Schema(code=ID(stored=True, unique=True),
                      title=TEXT(stored=True),
                      text=TEXT(vector=True, analyzer=ANALYZER))


# Schema for storing and indexing chapters in whoosh database
THERAPY_SCHEMA = Schema(code=ID(stored=True, unique=True),
                        title=TEXT(stored=True),
                        text=TEXT(vector=True, analyzer=ANALYZER))


# Map index name to schema
SCHEMA_MAP = {'atc': ATC_SCHEMA, 'icd': ICD_SCHEMA,
              'medicin': MEDIC_SCHEMA, 'therapy': THERAPY_SCHEMA}


def get_empty_indices():
    """Check if indices exists and contains documents."""
    classes = [ATC, ICD, Medicin, Therapy]
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


def main(script, command='', index=''):
    """Store data in whoosh index, or clean indices or search.

    Usage: python3 index.py <build|store|clear|search> [index]
    """
    # Store all objects in index
    if command == 'build':
        populate_all()
        empty = get_empty_indices()
        for cls in empty:
            store_objects_in_index(cls)
        return

    classes = [ATC, ICD, Medicin, Therapy]
    if index:
        classes = [i for i in classes if i._NAME == index]

    # Store objects in index
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

    # Search in index
    elif command == 'search':
        cls = classes[-1]
        pass

    # Unknown command
    else:
        print("Unknown command '%s'" % command)
        print("Usage: python3 index.py <build|store|clear|search> [index]")
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
