#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for handling patient cases and performing the project tasks.
"""
import sys
import os
from operator import itemgetter

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from schemas import ATC_SCHEMA, ICD10_SCHEMA, INDEX_DIR


def read_cases_from_files(folder_or_path):
    # Find case paths if path is a folder
    paths = []
    if not os.path.isdir(folder_or_path):
        paths.append(folder_or_path)
    else:
        for path in os.listdir(folder_or_path):
            full_path = os.path.normpath(os.path.join(folder_or_path, path))
            if not os.path.isdir(full_path):
                paths.append(full_path)

    # Read in lines from case files
    cases = {}
    for path in paths:
        filename, ext = os.path.splitext(os.path.split(path)[1])
        if ext == '.txt' and filename.startswith('case'):
            with open(path) as f:
                lines = [i.strip() for i in f.readlines()]
                cases[filename] = [i for i in lines if i]

    return cases


def task_1a(cases):
    """Perform task 1 A. Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname='icd10')
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:

        print("Case:Line - Results")
        for case, lines in sorted(cases.items(), key=itemgetter(0)):

            i = 0
            for line in lines:
                q = qp.parse(line)
                results = searcher.search(q)

                i += 1
                print("%s:%i - %i" % (case, i, 0))
                print(results[0:2])


def task_2(cases):
    """Perform task 2. Search through ATC codes."""
    pass


TASKS = {'1a': task_1a, '2': task_2}


def main(script, task='', case='', output=''):
    """Perform project tasks on cases.

    'task' is the project task to run, optional.
    'case' is a path to the case to run, optional.
    'output' is the output to generate, optional.
    Usage: 'python3 cases.py [task] [case] [latex|json]'.
    """
    # Handle cases
    if '.txt' in task:
        output = case
        case = task
        task = ''
    if not case:
        case = 'etc/'
    cases = read_cases_from_files(case)
    print("Loaded '%s' cases from '%s'" % (len(cases), case))

    #icd10_case_search(cases)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
