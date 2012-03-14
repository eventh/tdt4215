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
from tasks import OUTPUT_FOLDER
from data import (ATC, ICD, Therapy, PatientCase,
                  get_stopwords, get_medical_terms)


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
    words = sorted(get_stopwords())
    caption = '\\caption{Norwegian stopwords\\label{tab:stopwords}}\n'
    #A - D & D - H & H - K & K - N & N - S & S - Å \\
    _generate_columned_table(words, 6, 'stopwords', caption)


def generate_medical_terms_table():
    """Generate a LaTeX table with all medical terms."""
    words = sorted(get_medical_terms())
    caption = '\\caption{Medical terms\\label{tab:medicalterms}}\n'
    _generate_columned_table(words, 4, 'medicalterms', caption)


def _generate_columned_table(words, columns, name, caption='\n'):
    filename = '%s/%s.tex' % (OUTPUT_FOLDER, name)
    count = len(words)
    step = (count // columns) + 1
    words = list(words) + [''] * columns
    heading = ' & '.join('%s - %s' % (words[step*i][0],
                words[min(step*(i+1), count)-1][0]) for i in range(columns))

    with open(filename, 'w') as f:
        f.write(
r'''\begin{table}[htbp] \footnotesize \center
%s\begin{tabular}{%s}
    \toprule
    %s \\
    \midrule
''' % (caption, ' '.join(['l'] * columns), heading.upper()))
        for i in range(step):
            args = tuple([words[i+(step*j)] for j in range(columns)])
            string = '    ' + ' & '.join(['%s'] * columns) + '\\\\\n'
            f.write(string % args)

        f.write('    \\bottomrule\n\\end{tabular}\n\\end{table}\n\n\n')
    print("Dumped %i terms to '%s'" % (count, filename))
    print()


def generate_cases_table():
    """Generate LaTeX tables for patient cases."""
    cases = PatientCase.ALL
    filename = '%s/cases.tex' % OUTPUT_FOLDER
    with open(filename, 'w') as f:
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


def calculate_case_statistics():
    terms = get_medical_terms()
    print("Case | Terms | Medical terms")
    for code, case in sorted(PatientCase.ALL.items()):
        print(' | '.join((code, str(len(case.vector)),
                str(len([i for i in case.vector.keys() if i in terms])))))
    print()


def main(script):
    """Run all the functions in this module."""
    data.main()  # Populate all objects

    calculate_chapter_statistics()
    calculate_case_statistics()
    generate_stopwords_table()
    generate_medical_terms_table()
    generate_cases_table()


if __name__ == '__main__':
    main(*sys.argv)
