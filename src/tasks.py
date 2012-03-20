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
from collections import OrderedDict, defaultdict, Counter

from whoosh.qparser import QueryParser, OrGroup

from index import create_or_open_index, get_empty_indices
from data import (ATC, ICD, Therapy, PatientCase,
                  populate_all, get_medical_terms)


OUTPUT_FOLDER = 'output'  # Folder for storing json/tex files in.


def task_1(case_or_chapter):
    """Task 1: Search through ICD-10 codes."""
    return _index_searcher(ICD, 'label', case_or_chapter, 9, 1.5)


def task_1_alt(case_or_chapter):
    """Task 1 alternative: Search through ICD-10 codes."""
    return _index_searcher(ICD, 'description', case_or_chapter, 11, 3)


def task_2(case_or_chapter):
    """Task 2: Search through ATC codes."""
    return _index_searcher(ATC, 'title', case_or_chapter, 7, 2)


def task_3(case, limit=10):
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

    return [('%.2f' % s, str(c)) for c, s in
            sorted(results, key=itemgetter(1), reverse=True)[:limit]]


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


def task_5(case):
    """Task 5: Exchange evaluations"""
    pass


def task_6a(case, limit=10):
    """Task 6 A: Rank relevant chapters by using task 1 and 2 results."""
    # Load task 1 and 2 results
    def load(cls, task, attr, code_cls, code_attr):
        if not hasattr(list(cls.ALL.values())[-1], attr):
            if not hasattr(code_cls, code_attr):
                setattr(code_cls, code_attr, defaultdict(list))
            with open('etc/%s.json' % task, 'r') as f:
                for cls_code, lines in json.load(f).items():
                    codes = []
                    for i, line in sorted(lines.items()):
                        codes += line
                    setattr(cls.ALL[cls_code], attr, codes)

                    for code in codes:
                        getattr(code_cls, code_attr)[code].append(cls_code)

    load(PatientCase, 'task1a', '_icd_codes', ICD, '_case_map')
    load(PatientCase, 'task2a', '_atc_codes', ATC, '_case_map')
    load(Therapy, 'task1b', '_icd_codes', ICD, '_chapter_map')
    load(Therapy, 'task2b', '_atc_codes', ATC, '_chapter_map')

    # Get all relevant chapters, scored for each hit, also get parent codes
    counter = Counter()
    def count_chapter(code, cls, weight):
            codes = cls._chapter_map.get(code, [])
            counter.update({i: weight * codes.count(i) for i in set(codes)})

    for code in case._icd_codes:
        count_chapter(code, ICD, 1)
        for other in [i.code for i in ICD.ALL.values() if ICD.ALL[code].parent
                        and i.code.startswith(ICD.ALL[code].parent)]:
            count_chapter(other, ICD, 0.1)

    for code in case._atc_codes:
        count_chapter(code, ATC, 1)
        for other in [i.code for i in ATC.ALL if code.startswith(i.code)]:
            count_chapter(other, ATC, 0.1)

    scored = dict(counter.items())

    # Boost parents with max of children and parent ++
    for depth in range(4, 0, -1):
        parent = lambda code: code.rsplit('.', 1)[0]
        updated = {}
        for chapter, score in scored.items():
            if chapter.count('.') == depth:
                obj = parent(chapter)
                similars = [s for c, s in scored.items() if s > 0.3 and
                                obj == parent(c) and c.count('.') == depth]
                if len(similars) > 1:
                    updated[obj] = (0.5 + len(similars) / 10 +
                                    max([scored.get(obj, 0)] + similars))
        scored.update(updated)

    return [('%.2f' % s, str(Therapy.ALL[c])) for c, s in
            sorted(scored.items(), key=itemgetter(1), reverse=True)[:limit]]


def task_6b(case, limit=10):
    """Task 6 B: Improve task 3 ranking."""
    res3 = Counter({c: float(s) * 200 for s, c in task_3(case, 1000)})
    res6 = Counter({c: float(s) for s, c in task_6a(case, 1000)})
    overall = res3 + res6
    return [('%.2f' % j, str(i)) for i, j in
            sorted(overall.items(), key=itemgetter(1), reverse=True)[:limit]]


def task_7(case):
    """Match results with gold standard."""
    pass


def _index_searcher(cls, field, obj, lower=2, distance=2, max=2):
    """Search a specific 'field' on the 'cls' index."""
    ix = create_or_open_index(cls)
    qp = QueryParser(field, schema=ix.schema, group=OrGroup)

    results = []
    with ix.searcher() as searcher:
        for line in obj.text.split('\n'):
            q = qp.parse(line)
            objs = searcher.search(q)

            codes = []
            for hit in objs:
                if ((hit.score < lower and codes) or
                        (hit.score + distance < objs[0].score) or
                        (len(codes) > max)):
                    break
                codes.append(hit['code'])

            results.append(codes)
    return results


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
    if isinstance(codes, str):
        return codes
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
            for i, codes in enumerate(lines, 1):
                obj[i] = codes[:5]
            output[case] = obj
        json.dump(output, f, indent=4)
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
    %s \\
    \midrule
''' % (task, task, ' & '.join(fields)))

        nr = 'first'
        for case_nr, lines in results.items():
            if nr != 'first':
                f.write('\t\\addlinespace\n')

            nr = case_nr
            for i, codes in enumerate(lines, 1):
                if len(fields) == 4:
                    args = (nr, str(i), codes[0], _code_list_to_str(codes[1]))
                else:
                    args = (nr, str(i), _code_list_to_str(codes))
                f.write('    %s \\\\\n' % (' & '.join(args)))
                nr = ''

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

        for i, codes in enumerate(lines, 1):
            if len(fields) == 4:
                args = (case, str(i), codes[0], _code_list_to_str(codes[1]))
            else:
                args = (case, str(i), _code_list_to_str(codes))
            print(' | '.join(args))

        print()


# Maps valid output arguments to functions which generates output
OUTPUTS = {'json': output_json, 'latex': output_latex, '': output_print}


# Maps valid task names to functions which perform tasks
CASE_TASKS = {'1a': task_1, '1a2': task_1_alt, '2a': task_2,
              '3': task_3, '4': task_4, '6a': task_6a, '6b': task_6b}
CHAPTER_TASKS = {'1b': task_1, '1b2': task_1_alt, '2b': task_2}


# Maps task name to output fields
TASK_FIELDS = {'1a': ('Clinical note', 'Sentence', 'ICD-10'),
               '1a2': ('Clinical note', 'Sentence', 'ICD-10'),
               '1b': ('Chapter', 'Sentence', 'ICD-10'),
               '1b2': ('Chapter', 'Sentence', 'ICD-10'),
               '2a': ('Clinical note', 'Sentence', 'ATC'),
               '2b': ('Chapter', 'Sentence', 'ATC'),
               '3': ('Case', 'Rank','Score', 'Relevant chapter'),
               '4': ('Case', 'Rank', 'Relevant chapter'),
               '6a': ('Case', 'Rank', 'Score', 'Relevant chapter'),
               '6b': ('Case', 'Rank', 'Score', 'Relevant chapter')}


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
