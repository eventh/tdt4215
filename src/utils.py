#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for doing misc project stuff.

Probably generating some useless tables etc.
"""
import sys
from collections import Counter

from data import ATC, ICD, Therapy, PatientCase


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


def generate_cases_table():
    """Generate LaTeX tables for patient cases."""
    filename = 'output/cases.tex'
    with open(filename, 'w') as f:
        for nr, obj in sorted(PatientCase.ALL.items()):
            rows = [('c', 'X'), ('\#', 'Lines (stopwords removed)')]
            for i, line in enumerate(obj.text.split('\n')):
                rows.append((str(i + 1), line.replace('%', '\%')))
            text = create_latex_table('case%s' % nr,
                                      'Patient case %s' % nr, rows, True)
            f.write(text)
    print("Dumped %i patient cases to '%s'" % (len(PatientCase.ALL), filename))
    print()


def _generate_columned_table(words, columns, name, caption):
    """Generate LaTeX table of lot of words."""
    count = len(words)
    step = (count // columns) + 1
    words = list(words) + [''] * columns
    rows = [['l'] * columns]
    rows.append('%s - %s' % (words[step * i][0].upper(),
                             words[min(step * (i + 1), count) - 1][0].upper())
                                    for i in range(columns))
    for i in range(step):
        rows.append([words[i+(step*j)] for j in range(columns)])

    create_latex_table(name, caption, rows, filename='output/%s.tex' % name)
    print()


def create_latex_table(label, caption, rows, tabularx=False, filename=None):
    """Create a LaTeX table.

    'label' is a string with the table label for referencing.
    'caption' is a string with the table caption.
    'rows' is a list of table rows, first row is the table layout,
        second row is column headers and rest is rows of fields.
    'tabularx' creates tabular table if False, tabularx if True.
    'filename' is a filename to save the table to.

    returns a string with the table nicely formatted.
    """
    tabx = 'x}{\\textwidth' if tabularx else ''
    end = 'x' if tabularx else ''
    text = r'''\begin{table}[htbp] \footnotesize \center
\caption{%s\label{tab:%s}}
\begin{tabular%s}{%s}
    \toprule
    %s \\
    \midrule
''' % (caption, label, tabx, ' '.join(rows[0]), ' & '.join(rows[1]))
    for row in rows[2:]:
        text += '    ' + ' & '.join(row) + ' \\\\\n'
    text += '    \\bottomrule\n\\end{tabular%s}\n\\end{table}\n\n' % end

    if filename is not None:
        with open(filename, 'w') as f:
            f.write(text)
        print("Dumped %i %s to '%s'" % (len(rows) - 2, label, filename))

    return text


def calculate_case_statistics():
    """Calculate statistics of patient cases."""
    terms = get_medical_terms()
    print("Case | Terms | Medical terms")
    for code, case in sorted(PatientCase.ALL.items()):
        print(' | '.join((code, str(len(case.vector)),
                str(len([i for i in case.vector.keys() if i in terms])))))
    print()


def main(script):
    """Run all the functions in this module."""
    import data
    data.main()  # Populate all objects

    # Generate a LaTeX table with all stopwords
    _generate_columned_table(sorted(data.get_stopwords()),
                             6, 'stopwords', 'Norwegian stopwords')

    # Generate a LaTeX table with all medical terms
    _generate_columned_table(sorted(data.get_medical_terms()),
                             3, 'medicalterms', 'Medical terms')

    generate_cases_table()
    calculate_chapter_statistics()
    calculate_case_statistics()


if __name__ == '__main__':
    main(*sys.argv)
