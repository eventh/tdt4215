#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for doing misc project stuff.

Probably generating some useless tables etc.
"""
import sys
from collections import Counter

from nlh import populate_chapters, Chapter
from codes import populate_codes, ATC, ICD10
from tasks import read_stopwords, OUTPUT_FOLDER


def calculate_chapter_statistics():
    """Print out therapy chapter statistics."""
    print(calculate_chapter_statistics.__doc__)
    c_all = Counter([i.code.count('.') for i in Chapter.ALL])
    c_text = Counter([i.code.count('.') for i in Chapter.ALL if i.text])
    titles = ('Chapters', 'Sub', 'Sub*2', 'Sub*3', 'Sub*4')
    for i, title in enumerate(titles):
        space = ' ' * (8 - len(title))
        print("%s%s: %i (%i with text)" % (title, space, c_all[i], c_text[i]))
    print("Total   : %i (%i with text)" % (
            len(Chapter.ALL), sum(c_text.values())))

    sentences = lines = 0
    for obj in Chapter.ALL:
        if obj.text:
            lines += len([i for i in obj.text.split('\n') if i.strip()])
            sentences += len([i for i in obj.text.split('.') if i.strip()])
    print("Total amount of lines '\\n': %i" % lines)
    print("Total amount of sentences '.': %i" % sentences)
    print()


def generate_stopwords_table():
    """Generate a LaTeX table with all stopwords."""
    print(generate_stopwords_table.__doc__)
    columns = 6
    words = sorted(read_stopwords())
    count = len(words)
    step = (count // columns) + 1
    words.extend([''] * columns)

    filename = '%s/stopwords.tex' % OUTPUT_FOLDER
    with open(filename, 'w') as f:
        f.write(
r'''\begin{table}[htbp] \footnotesize \center
\caption{Stopwords\label{tab:stopwords}}
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


def main(script):
    populate_codes()
    populate_chapters()

    calculate_chapter_statistics()
    generate_stopwords_table()


if __name__ == '__main__':
    main(*sys.argv)
