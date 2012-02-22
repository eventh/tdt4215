#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for searching through different cases etc.
"""
import sys
import os
from operator import itemgetter

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from schemas import ICD10_SCHEMA, INDEX_DIR


# Folder where tasks are stored as .txt files.
TASK_DIR = 'etc/'


def read_cases_from_files(folder):
    cases = {}
    for path in os.listdir(folder):
        full_path = os.path.normpath(os.path.join(folder, path))
        filename, ext = os.path.splitext(path)
        if not os.path.isdir(full_path) and ext == '.txt':
            with open(full_path) as f:
                lines = [unicode(i, errors='ignore')
                            for i in f.readlines() if i]
            cases[filename.replace('case', '')] = lines
    return cases


def icd10_case_search(cases):
    ix = open_dir(INDEX_DIR, indexname='icd10')
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:

        print "Case:Line - Results"
        for case, lines in sorted(cases.items(), key=itemgetter(0)):

            i = 0
            for line in lines:
                q = qp.parse(line)
                results = searcher.search(q)

                i += 1
                print "%s:%i - %i" % (case, i, 0)
                print results[0:2]


def main(script):
    cases = read_cases_from_files(TASK_DIR)
    print "Loaded '%s' cases from '%s'" % (len(cases), TASK_DIR)

    icd10_case_search(cases)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
