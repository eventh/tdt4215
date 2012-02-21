#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for searching through different cases etc.
"""
import sys
import os
from operator import itemgetter

from search import search_icd10


TASK_DIR = 'etc/'


def read_cases_from_files(folder):
    cases = {}
    for path in os.listdir(folder):
        full_path = os.path.normpath(os.path.join(folder, path))
        filename, ext = os.path.splitext(path)
        if not os.path.isdir(full_path) and ext == '.txt':
            with open(full_path) as f:
                lines = [unicode(i, errors='ignore') for i in f.readlines()]
            cases[filename.replace('case', '')] = lines
    return cases


def icd10_case_search(cases):
    def result_handler(result):
        return len(result)

    print "Case:Line - Results"
    for case, lines in sorted(cases.items(), key=itemgetter(0)):
        i = 0
        for query in lines:
            if not query:
                continue
            i += 1
            results = search_icd10(query, result_handler)
            print "%s:%i - %i" % (case, i, results)


def main(script):
    cases = read_cases_from_files(TASK_DIR)
    print "Loaded '%s' cases from '%s'" % (len(cases), TASK_DIR)

    icd10_case_search(cases)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
