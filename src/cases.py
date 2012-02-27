#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for handling patient cases and performing the project tasks.

Runs all or specified project tasks, with all or specified patient cases.
Outputs either to stdout, or saves to JSON files or generates LaTeX tables.
"""
import sys
import os
import time
import json
from operator import itemgetter
from collections import OrderedDict

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from codes import ATC, ICD10, INDEX_DIR, is_indices_empty


OUTPUT_FOLDER = 'output'  # Folder for storing json/tex files in.


def read_stopwords():
    """Read in and return stop-words from file."""
    with open('etc/stoppord.txt', 'r') as f:
        return set(i.strip() for i in f.readlines())


def remove_stopwords(lines, words=read_stopwords()):
    """Remove stop-words from lines."""
    output = []
    for line in lines:
        line = ' '.join(i for i in line.strip().split(' ')
                                    if i.lower() not in words)
        if line:
            output.append(line)
    return output


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
                cases[filename] = remove_stopwords(f.readlines())

    return cases


def task_1a(lines):
    """Task 1 A: Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname=ICD10.NAME)
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in lines:
            q = qp.parse(line)
            objs = searcher.search(q)

            # Add up to 3 hits if they are higher than 9 and closer than 2
            codes = []
            for hit in objs:
                if ((hit.score < 9 and codes) or
                        (hit.score + 2 < objs[0].score) or
                        (len(codes) > 2)):
                    break
                codes.append(hit['code'])

            results.append(codes)
    return results


def task_1a_alt(lines):
    """Task 1 A: Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname=ICD10.NAME)
    qp = QueryParser('description', schema=ix.schema, group=OrGroup)
    # What about exclusions? NOT IN?

    results = []
    with ix.searcher() as searcher:
        for i, line in enumerate(lines):
            q = qp.parse(line)
            objs = searcher.search(q)

            # Add up to 3 hits if they are higher than 11 and closer than 3
            codes = []
            for hit in objs:
                if ((hit.score < 11 and codes) or
                        (hit.score + 3 < objs[0].score) or
                        (len(codes) > 2)):
                    break
                codes.append(hit['code'])

            results.append(codes)
    return results


def task_1b(lines):
    """Task 1 B: Search through Legemiddelhandboken."""
    return []


def task_2a(lines):
    """Task 2: Search through ATC codes."""
    ix = open_dir(INDEX_DIR, indexname=ATC.NAME)
    qp = QueryParser('name', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in lines:
            q = qp.parse(line)
            results.append([r['code'] for r in searcher.search(q)])
            #print("line %i: %s" % (i+1, line))
            #for k, hit in enumerate(objs[:5]):
            #    print('%i: %s - %s' % (k, hit['code'], hit['label']), hit.score)
            #    if k < 1:
            #        print("Matched:", ', '.join(i[1] for i in hit.matched_terms()))
    return results


def task_2b(lines):
    """Task 2 B: Search through Legemiddelhandboken."""
    return []


def _code_list_to_str(codes):
    """Convert a list of codes to a string of codes."""
    if not codes:
        return '.'
    if len(codes) > 6:
        codes = codes[:5] + ['...']
    return ', '.join(codes)


def output_json(task, results, fields=None):
    """Dump search results to a JSON file."""
    filename = '%s/task%s.json' % (OUTPUT_FOLDER, task)
    with open(filename, 'w') as f:
        output = OrderedDict()
        for case, lines in results.items():
            obj = OrderedDict()
            for i, codes in enumerate(lines):
                obj[i] = _code_list_to_str(codes)
            output[case] = obj
        json.dump({'task%s' % task: output}, f, indent=4)
    print("Dumped task %s results to '%s'" % (task, filename))


def output_latex(task, results, fields):
    """Dump search results to a LaTeX table."""
    filename = '%s/task%s.tex' % (OUTPUT_FOLDER, task)
    with open(filename, 'w') as f:
        f.write(
r'''\begin{table}[htbp] \footnotesize \center
\caption{Task %s\label{tab:task%s}}
\begin{tabular}{c c l}
    \toprule
    %s & %s & %s \\
    \midrule
''' % (task, task, fields[0], fields[1], fields[2]))

        nr = ''
        for case, lines in results.items():
            case_nr = case.replace('case', '')
            if nr == 'add':
                f.write('\t\\addlinespace\n')

            nr = case_nr
            for i, codes in enumerate(lines):
                f.write('\t%s & %s & %s \\\\\n' % (
                        nr, i + 1, _code_list_to_str(codes)))
                nr = ''
            nr = 'add'  # Hack

        f.write('\t\\bottomrule\n\\end{tabular}\n\\end{table}\n\n\n')

    print("Dumped task %s results to '%s'" % (task, filename))


def output_print(task, results, fields):
    """Print a table of search results.

    'task' is the name of the task we ran.
    'results' is a dict mapping case with results for the task.
    'fields' is the fields to represent in the output.
    """
    for case, lines in results.items():
        case_nr = case.replace('case', '')
        print("%s | %s | %s" % fields + " (task %s)" % task)
        print("--------------------------------------------")
        for i, codes in enumerate(lines):
            print("%s | %s | %s" % (case_nr, i + 1, _code_list_to_str(codes)))
        print()


def output_none(*args, **vargs):
    """Print nothing! WTF"""
    pass


# Maps valid task names to functions which perform tasks
TASKS = {'1a': task_1a, '1ab': task_1a_alt, '1b': task_1b,
        '2a': task_2a, '2b': task_2b}


# Maps task name to output fields
TASK_FIELDS = {'1a': ('Clinical note', 'Sentence', 'ICD-10'),
               '1ab': ('Clinical note', 'Sentence', 'ICD-10'),
               '1b': ('Chapter', 'Sentence', 'ICD-10'),
               '2a': ('Clinical note', 'Sentence', 'ATC'),
               '2b': ('Clinical note', 'Sentence', 'ATC')}


# Maps valid output arguments to functions which generates output
OUTPUTS = {'json': output_json, 'latex': output_latex,
           '': output_print, 'none': output_none}


def main(script, task='', case='', output=''):
    """Perform project tasks on cases.

    'task' is the project task to run, optional.
    'case' is a path to the case to run, optional.
    'output' is the output to generate, optional.
    Usage: 'python3 cases.py [task] [case] [latex|json]'.
    """
    # Check if indexes contains documents
    if is_indices_empty():
        print("You need to build indexes with codes.py first!")
        sys.exit(1)

    # Handle output
    if task in ('json', 'latex', 'none'):
        output = task
        task = ''
    if case in ('json', 'latex', 'none'):
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
    start_time = time.time()
    for task_name, func in sorted(tasks.items(), key=itemgetter(0)):
        now = time.time()
        results = OrderedDict()
        for case_name, lines in sorted(cases.items(), key=itemgetter(0)):
            results[case_name] = func(lines)
        output_handler(task_name, results, TASK_FIELDS[task_name])
        print("Performed '%s' in %.2f seconds" % (
                func.__doc__, time.time() - now))

    if len(tasks) > 1:
        print("Ran %s tasks in %.2f seconds" % (
                len(tasks), time.time() - start_time))

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
