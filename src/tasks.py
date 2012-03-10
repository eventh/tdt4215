#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for handling patient cases and performing the project tasks.

Runs all or specified project tasks, with all or specified patient cases.
Outputs either to stdout, or saves to JSON files or generates LaTeX tables.

Usage: python3 <task> [<case|chapter>] [latex|json]
"""
import sys
import os
import time
import re
import json
from operator import itemgetter
from collections import OrderedDict, Counter

from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup

from codes import ATC, ICD10, INDEX_DIR, is_indices_empty, populate_codes
from nlh import Chapter, populate_chapters


OUTPUT_FOLDER = 'output'  # Folder for storing json/tex files in.


def read_stopwords():
    """Read in and return stop-words from file."""
    with open('etc/stoppord.txt', 'r') as f:
        return set(i.strip() for i in f.readlines() if i.strip())


def remove_stopwords(lines, words=read_stopwords()):
    """Remove stop-words from lines."""
    output = []
    for line in lines:
        line = ' '.join(i for i in line.strip().split(' ')
                                    if i.lower() not in words)
        if line:
            if line[-1] == '.':
                line = line[:-1]  # Remove period from queries
            output.append(line)
    return output


def read_cases_from_files(folder_or_path):
    """Read lines from case files in 'folder_or_path'."""
    if not os.path.exists(folder_or_path):
        print("Invalid case path: %s" % folder_or_path)
        sys.exit(2)

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
                case_nr = filename.replace('case', '')
                cases[case_nr] = remove_stopwords(f.readlines())

    return cases


def task_1(lines):
    """Task 1: Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname=ICD10.NAME)
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in lines:
            q = qp.parse(line)
            objs = searcher.search(q)

            # Add up to 3 hits if they are higher than 9 and closer than 1.5
            codes = []
            for hit in objs:
                if ((hit.score < 9 and codes) or
                        (hit.score + 1.5 < objs[0].score) or
                        (len(codes) > 2)):
                    break
                codes.append(hit['code'])

            results.append(codes)
    return results


def task_1_alt(lines):
    """Task 1 alternative: Search through ICD10 codes."""
    ix = open_dir(INDEX_DIR, indexname=ICD10.NAME)
    qp = QueryParser('description', schema=ix.schema, group=OrGroup)
    # What about exclusions? NOT IN?

    results = []
    with ix.searcher() as searcher:
        for line in lines:
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


def task_2(lines):
    """Task 2: Search through ATC codes."""
    ix = open_dir(INDEX_DIR, indexname=ATC.NAME)
    qp = QueryParser('name', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for i, line in enumerate(lines):
            q = qp.parse(line)
            objs = searcher.search(q)

            # Add up to 3 hits if they are higher than 7 and closer than 2
            codes = []
            for hit in objs:
                if ((hit.score < 7 and codes) or
                        (hit.score + 2 < objs[0].score) or
                        (len(codes) > 2)):
                    break
                codes.append(hit['code'])

            results.append(codes)
    return results


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
        for case_nr, lines in results.items():
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
        print("%s | %s | %s" % fields + " (task %s)" % task)
        print("--------------------------------------------")
        for i, codes in enumerate(lines):
            print("%s | %s | %s" % (case, i + 1, _code_list_to_str(codes)))
        print()


def output_none(*args, **vargs):
    """Print nothing! WTF"""
    pass


# Maps valid output arguments to functions which generates output
OUTPUTS = {'json': output_json, 'latex': output_latex,
           '': output_print, 'none': output_none}


# Maps valid task names to functions which perform tasks
CASE_TASKS = {'1a': task_1, '1a2': task_1_alt, '2a': task_2}
CHAPTER_TASKS = {'1b': task_1, '1b2': task_1_alt, '2b': task_2}


# Maps task name to output fields
TASK_FIELDS = {'1a': ('Clinical note', 'Sentence', 'ICD-10'),
               '1a2': ('Clinical note', 'Sentence', 'ICD-10'),
               '1b': ('Chapter', 'Sentence', 'ICD-10'),
               '1b2': ('Chapter', 'Sentence', 'ICD-10'),
               '2a': ('Clinical note', 'Sentence', 'ATC'),
               '2b': ('Chapter', 'Sentence', 'ATC')}


def _perform_task(task_name, func, inputs, output, progress=False):
    """Perform a specific task."""
    now = time.time()
    results = OrderedDict()

    i = 0
    for name, lines in sorted(inputs.items(), key=itemgetter(0)):
        if progress:
            i += 1
            print("[%i] %s" % (i, name))
        results[name] = func(lines)

    output(task_name, results, TASK_FIELDS[task_name])
    print("Performed '%s' in %.2f seconds" % (func.__doc__, time.time() - now))


def main(script, task='', case='', output=''):
    """Perform project tasks.

    'task' is the project task to run.
    'case' is a path to the case to run, optional.
    'output' is the output to generate, optional.
    Usage: python3 <task> [<case|chapter>] [latex|json]
    """
    if not task:
        print("Usage: python3 <task> [<case|chapter>] [latex|json]")
        sys.exit(2)

    if is_indices_empty():
        print("You need to build indexes with codes.py first!")
        sys.exit(1)

    if case and case in OUTPUTS:
        output = case
        case = ''
    if output in ('json', 'latex') and not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)
    if output not in OUTPUTS:
        print("Unknown output %s, valid:" % output, ', '.join(OUTPUTS.keys()))
        sys.exit(2)

    # Perform a task which uses patient cases as input
    if task == '3':
        task_3()
    elif task in CASE_TASKS:
        if not case:
            case = 'etc/'
        cases = read_cases_from_files(case)
        print("Loaded %s cases from '%s'" % (len(cases), case))
        _perform_task(task, CASE_TASKS[task], cases, OUTPUTS[output])

    # Perform a task which uses chapters as input
    elif task in CHAPTER_TASKS:
        chapters = {i.code: remove_stopwords(i.text.split('\n')) for i in
                        populate_chapters() if (not case or case == i.code)}
        if not chapters:
            print("Unknown chapter code: %s" % case)
            sys.exit(2)
        _perform_task(task, CHAPTER_TASKS[task], chapters,
                      OUTPUTS[output], progress=True)

    else:
        print("Unknown task '%s', valid tasks are: %s" % (task,
            ', '.join(list(CASE_TASKS.keys()) + list(CHAPTER_TASKS.keys()))))
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
