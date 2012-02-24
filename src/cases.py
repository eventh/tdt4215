#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for handling patient cases and performing the project tasks.
"""
import sys
import os
import time
from operator import itemgetter
from functools import partial

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from schemas import ATC_SCHEMA, ICD10_SCHEMA, INDEX_DIR


def read_cases_from_files(folder_or_path):
    """Read lines from case files in 'folder_or_path'."""
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


def task_1a(lines, output_handler):
    """Task 1 A: Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname='icd10')
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    with ix.searcher() as searcher:
        for line in lines:
            q = qp.parse(line)

            results = searcher.search(q)
            output_handler(results)
            break # TODO


def task_2(lines, output_handler):
    """Task 2: Search through ATC codes."""
    ix = open_dir(INDEX_DIR, indexname='atc')
    qp = QueryParser('name', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for i, line in enumerate(lines):
            q = qp.parse(line)
            results.append((i, [r['code'] for r in searcher.search(q)]))
    output_handler(results)


def output_json(task, case, results):
    pass


def output_latex(task, case, results):
    pass


def output_print(task, case, results):
    print("Results from task %s - %s" % (task, case))
    print("----------------------------")
    for line, codes in results:
        if not codes:
            codes = '.'
        else:
            if len(codes) > 6:
                codes = codes[:6] + ['...']
            codes = ', '.join(codes)
        print("%s:%s - %s" % (case, line, codes))
    print()


# Maps valid task names to functions which perform tasks
TASKS = {'1a': task_1a, '2': task_2}


# Maps valid output arguments to functions which generates output
OUTPUTS = {'json': output_json, 'latex': output_latex, '': output_print}


def main(script, task='', case='', output=''):
    """Perform project tasks on cases.

    'task' is the project task to run, optional.
    'case' is a path to the case to run, optional.
    'output' is the output to generate, optional.
    Usage: 'python3 cases.py [task] [case] [latex|json]'.
    """
    # Handle output
    if task in ('json', 'latex'):
        output = task
        task = ''
    if case in ('json', 'latex'):
        output = case
        case = ''
    if output not in OUTPUTS:
        print("Unknown output '%s', valid are: %s" % (
                output, ', '.join(OUTPUTS.keys())))
        sys.exit(2)
    output_handler = OUTPUTS[output]

    # Handle and read in cases
    if '.txt' in task:
        output = case
        case = task
        task = ''
    if not case:
        case = 'etc/'
    cases = read_cases_from_files(case)
    print("Loaded %s cases from '%s'" % (len(cases), case))

    # Handle task argument
    if task in TASKS:
        tasks = {task: TASKS[task]}
    elif not task:
        tasks = TASKS
    else:
        print("Unknown task '%s', valid tasks are: %s" % (
                task, ', '.join(TASKS.keys())))
        sys.exit(2)

    # Perform tasks, one at a time, one case at a time
    for task_name, func in tasks.items():
        now = time.time()
        for case_name, lines in sorted(cases.items(), key=itemgetter(0)):
            output_func = partial(output_handler, task_name, case_name)
            func(lines, output_func)

        print("Performed '%s' in %.2f seconds" % (
                func.__doc__, time.time() - now))

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
