#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for doing misc project stuff.

Probably generating some useless tables etc.
"""
import sys
from collections import Counter
from operator import itemgetter

import data
from data import ATC, ICD, Therapy, PatientCase, get_stopwords
from tasks import OUTPUT_FOLDER


def calculate_chapter_statistics():
    """Print out therapy chapter statistics."""
    c_all = Counter([i.code.count('.') for i in Therapy.ALL.values()])
    c_text = Counter([i.code.count('.') for i in Therapy.ALL.values() if i.text])
    titles = ('Chapters', 'Sub', 'Sub*2', 'Sub*3', 'Sub*4')
    for i, title in enumerate(titles):
        space = ' ' * (8 - len(title))
        print("%s%s: %i (%i with text)" % (title, space, c_all[i], c_text[i]))
    print("Total   : %i (%i with text)" % (
            len(Therapy.ALL), sum(c_text.values())))

    sentences = lines = 0
    for obj in Therapy.ALL.values():
        if obj.text:
            lines += len([i for i in obj.text.split('\n') if i.strip()])
            sentences += len([i for i in obj.text.split('.') if i.strip()])
    print("Total amount of lines '\\n': %i" % lines)
    print("Total amount of sentences '.': %i" % sentences)
    print()


def generate_stopwords_table():
    """Generate a LaTeX table with all stopwords."""
    columns = 6
    words = sorted(get_stopwords())
    count = len(words)
    step = (count // columns) + 1
    words.extend([''] * columns)

    filename = '%s/stopwords.tex' % OUTPUT_FOLDER
    with open(filename, 'w') as f:
        f.write(
r'''
\chapter{Stop words}
\autoref{tab:stopwords} contains a list of Norwegian stop words used on search
queries such as patient cases and therapy chapters.
An initial list were %% TODO: add a reference to
Additional words with low relevenance, but which are frequently used in
patient cases, have been added.

\begin{table}[htbp] \footnotesize \center
\caption{Norwegian stop words\label{tab:stopwords}}
\begin{tabular}{%s}
    \toprule
    A - D & D - H & H - K & K - N & N - S & S - Å \\
    \midrule
''' % (' '.join(['l'] * columns)))
        for i in range(step):
            tmp = tuple([words[i+(step*j)] for j in range(columns)])
            f.write('    %s & %s & %s & %s & %s & %s \\\\\n' % tmp)

        f.write('    \\bottomrule\n\\end{tabular}\n\\end{table}\n\n\n')
    print("Dumped %i stopwords to '%s'" % (count, filename))
    print()


def generate_cases_table():
    """Generate LaTeX tables for patient cases."""
    cases = PatientCase.ALL
    filename = '%s/cases.tex' % OUTPUT_FOLDER
    with open(filename, 'w') as f:
        f.write(
r'''\chapter{Patient cases}
This chapter contains patient cases used as input in this project.
Norwegian stop words have been removed from these patient cases.
''')

        for case_nr, obj in sorted(cases.items()):
            f.write(
r'''\begin{table}[htbp] \footnotesize \center
\caption{Patient case %s\label{tab:pcase%s}}
\begin{tabularx}{\textwidth}{c X}
    \toprule
    \# & Lines (stop words removed) \\
    \midrule
''' % (case_nr, case_nr))

            for i, line in enumerate(obj.text.split('\n')):
                f.write('\t%i & %s \\\\\n' % (i + 1, line.replace('%', '\%')))

            f.write('\t\\bottomrule\n\\end{tabularx}\n\\end{table}\n\n\n')

    print("Dumped %i patient cases to '%s'" % (len(cases), filename))
    print()


def main(script):
    """Run all the functions in this module."""
    data.main()  # Populate all objects

    calculate_chapter_statistics()
    generate_stopwords_table()
    generate_cases_table()


if __name__ == '__main__':
    main(*sys.argv)
