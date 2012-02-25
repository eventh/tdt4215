#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for handling patient cases and performing the project tasks.
"""
import sys
import os
import time
import json
from operator import itemgetter
from functools import partial
from collections import OrderedDict

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from schemas import ATC_SCHEMA, ICD10_SCHEMA, INDEX_DIR


OUTPUT_FOLDER = 'output'  # Folder for storing json/tex files in.


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


def task_1a(lines):
    """Task 1 A: Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname='icd10')
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in lines:
            q = qp.parse(line)
            results.append((i + 1, [r['short'] for r in searcher.search(q)]))
    return results


def task_2(lines):
    """Task 2: Search through ATC codes."""
    ix = open_dir(INDEX_DIR, indexname='atc')
    qp = QueryParser('name', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for i, line in enumerate(lines):
            q = qp.parse(line)
            results.append((i + 1, [r['code'] for r in searcher.search(q)]))
    return results


def _code_list_to_str(codes):
    """Convert a list of codes to a string of codes."""
    if not codes:
        return '.'
    if len(codes) > 6:
        codes = codes[:6] + ['...']
    return ', '.join(codes)


def output_json(task, case, results):
    """Dump search results to a JSON file."""
    filename = '%s/task%s_%s.json' % (OUTPUT_FOLDER, task, case)
    with open(filename, 'w') as f:
        obj = OrderedDict()
        for line, codes in results:
            obj[line] = _code_list_to_str(codes)
        json.dump({case: obj}, f, indent=4)
    print("Dumped task %s %s results to '%s'" % (task, case, filename))


def output_latex(task, results):
    """Dump search results to a LaTeX table."""
    filename = '%s/task%s.tex' % (OUTPUT_FOLDER, task)
    with open(filename, 'w') as f:
        for case, tmp in results.items():
            case_nr = case.replace('case', '')

            f.write(
r'''\begin{table}[htbp] \footnotesize \center
\caption{Task %s, Clinical note %s \label{tab:t%sc%s}}
\begin{tabularx}{\textwidth}{c c X}
    \toprule
    Clinical note & Sentence & ICD-10 \\
    \midrule
''' % (task, case_nr, task, case_nr))

            for line, codes in tmp:
                f.write('\t %s & %s & %s \\\\\n' % (
                        case_nr, line, _code_list_to_str(codes)))
            f.write('\t\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n\n')

    print("Dumped task %s results to '%s'" % (task, filename))


def output_print(task, results):
    """Print a table of search results."""
    for case, tmp in results.items():
        print("Results from task %s - %s" % (task, case))
        print("--------------------------------------------")
        for line, codes in tmp:
            print("%s:%s - %s" % (case, line, _code_list_to_str(codes)))
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
    if output in ('json', 'latex') and not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)
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
        results = OrderedDict()
        for case_name, lines in sorted(cases.items(), key=itemgetter(0)):
            results[case_name] = func(lines)
        output_handler(task_name, results)
        print("Performed '%s' in %.2f seconds" % (
                func.__doc__, time.time() - now))

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
