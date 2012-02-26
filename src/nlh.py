#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing html documents from 'norsk legemiddelhåndbok'.
"""
import sys
from html.parser import HTMLParser


def preprocess_html_file(in_path, out_path):
    """Preprocess NLH HTML files.

    Change encoding to UTF-8 and remove unnecessary tags etc.
    """
    with open(in_path, 'r', encoding='iso-8859-1') as f1:
        with open(out_path, 'w') as f2:

            # Remove uneceseary carrier returns
            lines = (i.rstrip() for i in f.readlines())

            # Save lines to output file
            f2.write('\n'.join(i.rstrip() for i in f.readlines()))


def main(script):
    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
