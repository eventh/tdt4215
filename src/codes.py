#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for converting data to JSON, and for loading it into whoosh index.

Example usage:
To convert ICD XML file to JSON run the following command:
    'python3 codes.py ../data/icd10no.xml'

To insert ATC into whoosh index from JSON run the following command:
    'python3 codes.py etc/atcname.json store'
"""
import sys
import os
import time
import json
from collections import OrderedDict
from xml.etree import ElementTree


def is_indices_empty():
    """Check if indexes exists and contains documents."""
    if not os.path.isdir(INDEX_DIR):
        return True

    index_names = (ATC.NAME, ICD10.NAME)
    for name in index_names:
        if not exists_in(INDEX_DIR, indexname=name):
            return True
        ix = open_dir(INDEX_DIR, indexname=name)
        if ix.doc_count() < 1:
            return True

    return False


def create_index(cls):
    """Create index if necessary."""
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    if not exists_in(INDEX_DIR, indexname=cls.NAME):
        ix = create_in(INDEX_DIR, schema=cls.SCHEMA, indexname=cls.NAME)
        print("Created %s index '%s'" % (cls.__name__, cls.NAME))


