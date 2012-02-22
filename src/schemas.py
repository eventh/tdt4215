# -*- coding: utf-8 -*-
"""
A module for different whoosh schemas.
"""
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED


# Settings
INDEX_DIR = 'indexdir'

# Schema for storing and indexing ICD10 codes in whoosh database
ICD10_SCHEMA = Schema(short=ID(stored=True), label=TEXT, formatted=ID,
                      code=ID, type=TEXT, icpc2_label=TEXT, synonyms=TEXT,
                      terms=TEXT, inclusions=TEXT, exclusions=TEXT)
