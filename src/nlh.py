#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing html documents from 'norsk legemiddelhåndbok'.
"""
import os
import sys
import string
from html.parser import HTMLParser


class Chapter:

    ALL = []

    def __init__(self, type):
        Chapter.ALL.append(self)
        self.type = type

        self.title = None
        self.code = None
        self.text = ''
        self.links = []

        self.revidert = None

    def __str__(self):
        return '%s: %s' % (self.code, self.title)


class NLHParser(HTMLParser):

    _tags = ('strong', 'div', 'p', 'h2', 'h3', 'h4', 'h5', 'a')

    def __init__(self, *args, **vargs):
        super().__init__(*args, **vargs)

        self.actions = [] # Stack for actions to perform
        self.chapters = [] # Stack for chapters

    def _get_attr(self, attrs, key):
        """Get an attribute value from set of 'attrs'."""
        for tmp, value in attrs:
            if key == tmp:
                return value
        return None

    def _split_title(self, title):
        """Split a chapter into code and title."""
        i = 1
        while i < len(title):
            if title[i] not in string.digits and title[i] != '.':
                break
            i += 1
        return title[:i], title[i:]

    def handle_starttag(self, tag, attrs):
        """Handle the start of a HTML tag."""
        class_ = self._get_attr(attrs, 'class')
        action = 'pop'

        if tag == 'div' and class_ == 'seksjon3':
            self.chapters.append(Chapter('subchapter'))
            action = 'end_chapter'
        elif tag == 'div' and class_ == 'revidert' and self.chapters:
            action = 'store_revidert'
        elif tag == 'div' and class_ == 'def' and self.chapters:
            self.actions[-1][1].append('\n')
        elif tag == 'div' and class_ == 'tone' and self.chapters:
            self.actions[-1][1].append('\n')
        elif tag == 'p' and class_ == 'defa' and self.chapters:
            self.actions[-1][1].append(': ')
        elif tag == 'h3' and self.chapters:
            action = 'store_title'

        self.actions.append([action, []])

    def handle_data(self, data):
        """Handle text."""
        if self.actions:
            self.actions[-1][1].append(data.strip())

    def handle_endtag(self, tag):
        """Handle the end of an HTML tag."""
        def _add(data):
            if data and self.actions:
                self.actions[-1][1].append(data)

        if not self.actions:
            return

        action, data = self.actions.pop()
        data = ' '.join(i for i in ''.join(data).split(' ') if i)

        obj = self.chapters[-1] if self.chapters else None

        if action == 'store_title':
            obj.code, obj.title = self._split_title(data)
        elif action == 'store_revidert':
            obj.revidert = data
        elif action == 'end_chapter':
            obj.text += data
            print('Finished', obj)
            print(obj.text)
            self.chapters.pop()
        else:
            if data and self.actions:
                self.actions[-1][1].append(data)

    def handle_charref(self, name):
        """Handle weird html characters."""
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        if self.actions:
            self.actions[-1][1].append(c)


def preprocess_html_file(in_path, out_path):
    """Preprocess NLH HTML files.

    Change encoding to UTF-8 and remove unnecessary tags etc.
    """
    with open(in_path, 'r', encoding='iso-8859-1') as f1:
        with open(out_path, 'w') as f2:
            # Remove uneceseary carrier returns
            lines = [i.rstrip() for i in f1.readlines()]

            # Remove most of <head>
            lines = lines[:3] + lines[4:5] + lines[28:]

            # Remove footer
            lines = lines[:-10] + lines[-4:]

            # Save lines to output file
            f2.write('\n'.join(lines))


def parse_html_file(path):
    parser = NLHParser(strict=True)
    with open(path, 'r') as f:
        parser.feed(f.read())
        parser.close()


def main(script, path='', command='parse'):
    if not os.path.isfile(path):
        print("")
        sys.exit(2)

    if command == 'parse':
        parse_html_file(path)
    elif command.startswith('pre'):
        preprocess_html_file(path, path + 'l')

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
