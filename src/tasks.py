#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for performing the project tasks.

Runs a specified project task, with all or specified inputs.
Outputs either to stdout, or saves to JSON files or generates LaTeX tables.

Usage: python3 <task> [<case|chapter>] [latex|json]
"""
import os
import sys
import time
import json
from math import sqrt
from operator import itemgetter
from collections import OrderedDict

from whoosh.qparser import QueryParser, OrGroup

from index import create_or_open_index, get_empty_indices
from data import (ATC, ICD, Therapy, PatientCase,
                  populate_all, get_medical_terms)


OUTPUT_FOLDER = 'output'  # Folder for storing json/tex files in.


def task_1(obj):
    """Task 1: Search through ICD10 codes."""
    ix = create_or_open_index(ICD)
    qp = QueryParser('label', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in obj.text.split('\n'):
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


def task_1_alt(obj):
    """Task 1 alternative: Search through ICD10 codes."""
    ix = create_or_open_index(ICD)
    qp = QueryParser('description', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in obj.text.split('\n'):
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


def task_2(obj):
    """Task 2: Search through ATC codes."""
    ix = create_or_open_index(ATC)
    qp = QueryParser('title', schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in obj.text.split('\n'):
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


def task_3(case):
    """Task 3: Match patient cases to therapy chapters."""
    results = []
    for chapter in Therapy.ALL.values():
        matches = [chapter.vector[t] * v for t, v in
                        case.vector.items() if t in chapter.vector]

        if matches:
            AB_dotproduct = sum(matches)
            A_magnitude = sum(i ** 2 for i in chapter.vector.values())
            B_magnitude = sum(i ** 2 for i in case.vector.values())
            AB_magnitude = sqrt(A_magnitude) * sqrt(B_magnitude)
            results.append((chapter, AB_dotproduct / AB_magnitude))

    results.sort(key=itemgetter(1), reverse=True)
    return [[i] for i, v in results[:10]]


def task_4(case, medical=get_medical_terms()):
    """Task 4: Evaluate results from task 3."""
    #if not hasattr(PatientCase.ALL["1"], 'vector2'):
    #    from index import create_vectors, _tf_raw_freq, _idf_prob
    #    create_vectors(idf=_idf_prob, attr='vector2')  # B
    #    #create_vectors(tf=_tf_raw_freq, attr='vector2')  # C
    #    #create_vectors(tf=_tf_raw_freq, idf=_idf_prob, attr='vector3')  # D

    results = _task_4_search(case, medical)
    #results2 = _task_4_search(case, medical, 'vector3')
    #print("[%s]: Kendal Tau: %.3f" % (case.code, _kendall_tau(results, results2, 1000)))
    _task_4_print_terms(results)
    _task_4_precision(results)
    #_task_4_precision(results2)


def _task_4_print_terms(results, medical=get_medical_terms()):
    """Prints out terms/medical terms etc for task 4"""
    print("Rank | Chapter | Score | Relevant | Terms")
    for i, tmp in enumerate(results[:10]):
        obj, v, terms, rel = tmp
        r = 'Yes' if rel else 'No'
        b_terms = []
        for t in terms:
            b_terms.append('\\textbf{%s}' % t if t in medical else t)
        #print('\t%i & %s & %.4f & %s & %s \\\\' % (
        #        i+1, obj.code, v, r, ', '.join(b_terms)))
        print('%i | %s | %.4f | %s | %s' % (
                i+1, obj.code, v, r, ', '.join(terms)))


def _task_4_search(case, medical, attr='vector'):
    """Perform a task 4 search."""
    results = []
    case_vector = getattr(case, attr)
    for chapter in Therapy.ALL.values():
        chapter_vector = getattr(chapter, attr)

        matches = [chapter_vector[t] * v for t, v in
                        case_vector.items() if t in chapter_vector]

        if matches:
            AB_dotproduct = sum(matches)
            A_magnitude = sum(i ** 2 for i in chapter_vector.values())
            B_magnitude = sum(i ** 2 for i in case_vector.values())
            AB_magnitude = sqrt(A_magnitude) * sqrt(B_magnitude)

            terms = [t for t, v in case_vector.items() if t in chapter_vector]
            rel = [t for t in terms if t.lower() in medical]
            results.append((chapter, AB_dotproduct / AB_magnitude, terms, rel))

    return sorted(results, key=itemgetter(1), reverse=True)


def _task_4_precision(results, count=10, hack=[]):
    """Calculate precision at 'count' and R-precision."""
    rel_count = sum([0] + [1 for r in results[:count] if r[3]])
    r_precision = sum([0] + [1 for r in results[:rel_count] if r[3]])
    print('Precision at 10 (P@10): %i%%' % (rel_count * count))
    print("R-Precision (%i): %.2f" % (rel_count, r_precision / rel_count))
    hack.append((rel_count, r_precision / rel_count))
    if len(hack) == 8:
        print("Avg p: %.1f" % (sum(i for i, j in hack) * count / 8))
        print("Avg r: %.2f" % (sum(j for i, j in hack) / 8))


def _kendall_tau(result1, result2, K=10, hack=[]):
    """Calculate Kendall Tau Coefficient of two search results."""
    K = min(K, len(result1), len(result2))
    result1 = [i[0].code for i in result1[:K]]
    result2 = [i[0].code for i in result2[:K]]
    delta = 0
    for i, a in enumerate(result1):
        for j, b in enumerate(result1):
            if j < i:
                try:
                    rank1 = result2.index(a)
                except ValueError:
                    rank1 = K + 1
                try:
                    rank2 = result2.index(b)
                except ValueError:
                    rank2 = K + 1
                if rank1 < rank2:
                    delta += 1
    tau = 1.0 - ((2.0 * delta) / (K * (K - 1)))
    hack.append(tau)
    if len(hack) == 8:
        print("Avg: %.3f" % (sum(hack) / 8.0))
    return tau


def _code_list_to_str(codes):
    """Convert a list of codes to a string of codes."""
    if not codes:
        return '.'
    if len(codes) > 6:
        codes = codes[:5] + ['...']
    return ', '.join(str(i) for i in codes)


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
        print("%s" % ' | '.join(fields) + " (task %s)" % task)
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
CASE_TASKS = {'1a': task_1, '1a2': task_1_alt, '2a': task_2,
              '3': task_3, '4': task_4}
CHAPTER_TASKS = {'1b': task_1, '1b2': task_1_alt, '2b': task_2}


# Maps task name to output fields
TASK_FIELDS = {'1a': ('Clinical note', 'Sentence', 'ICD-10'),
               '1a2': ('Clinical note', 'Sentence', 'ICD-10'),
               '1b': ('Chapter', 'Sentence', 'ICD-10'),
               '1b2': ('Chapter', 'Sentence', 'ICD-10'),
               '2a': ('Clinical note', 'Sentence', 'ATC'),
               '2b': ('Chapter', 'Sentence', 'ATC'),
               '3': ('Case', 'Rank', 'Relevant chapter'),
               '4': ('Case', 'Rank', 'Relevant chapter')}


def _perform_task(task_name, func, inputs, output, progress=False):
    """Perform a specific task."""
    now = time.time()
    results = OrderedDict()

    i = 0
    for name, obj in sorted(inputs.items(), key=itemgetter(0)):
        if progress:
            i += 1
            print("[%i] %s" % (i, name))

        results[name] = func(obj)

    if list(results.values())[-1] is not None:
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

    if get_empty_indices():
        print("Empty indices, run 'python3 index.py build' first!")
        sys.exit(1)

    if case and case in OUTPUTS:
        output = case
        case = ''
    if output in ('json', 'latex') and not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)
    if output not in OUTPUTS:
        print("Unknown output %s, valid:" % output, ', '.join(OUTPUTS.keys()))
        sys.exit(2)

    populate_all()

    # Perform a task which uses patient cases as input
    if task in CASE_TASKS:
        cases = {name: obj for name, obj in PatientCase.ALL.items()
                    if (not case or name == case)}
        if not cases:
            print("Unknown patient case: %s" % case)
            sys.exit(2)
        _perform_task(task, CASE_TASKS[task], cases, OUTPUTS[output])

    # Perform a task which uses chapters as input
    elif task in CHAPTER_TASKS:
        chapters = {code: obj for code, obj in Therapy.ALL.items()
                        if (not case or case == obj.code)}
        if not chapters:
            print("Unknown therapy code: %s" % case)
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
