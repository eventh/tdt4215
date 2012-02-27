#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing html documents from 'norsk legemiddelhåndbok'.
"""
import os
import sys
from html.parser import HTMLParser


class Chapter:

    ALL = []

    def __init__(self, type):
        Chapter.ALL.append(self)
        self.type = type

        self.title = None
        self.code = None
        self.text = ''

    def __str__(self):
        return '%s - %s' % (self.code, self.title)


class MyHTMLParser(HTMLParser):

    _tags = ('strong', 'div', 'p', 'h2', 'h3', 'h4', 'h5', 'a')

    def __init__(self, *args, **vargs):
        super().__init__(*args, **vargs)

        self.action_stack = []
        self.data_stack = []
        self.current = None

    def _get_attr(self, attrs, key):
        for tmp, value in attrs:
            if key == tmp:
                return value
        return None

    def handle_starttag(self, tag, attrs):
        class_ = self._get_attr(attrs, 'class')
        action = None

        # Start a new subchapter
        if tag == 'div' and class_ == 'seksjon3':
            obj = Chapter('subchapter')
            action = 'end_chapter'
            self.current = obj

        # Record the title and code
        elif tag == 'h3' and self.current:
            action = 'store_title'

        if tag in self._tags and self.current:
            if not action:
                action = 'store_text'
            self.action_stack.append(action)
            #print("Pushed tag:", tag, action)
        else:
            self.action_stack.append('pop')
        self.data_stack.append([])

    def handle_data(self, data):
        if self.data_stack:
            self.data_stack[-1].append(data.strip())

    def handle_endtag(self, tag):
        action = self.action_stack.pop()
        data = ''.join(i for i in self.data_stack.pop() if i)
        data = ' '.join(i for i in data.split(' ') if i)
        if not self.current:
            return

        if tag in ('p', 'div', 'h5', 'h4'):
            if self.current.text and self.current.text[-1] != '\n':
                self.current.text += '\n'

        if action == 'store_title':
            self.current.code, self.current.title = data, data #TODO
        elif action == 'store_text':
            self.current.text += data
        elif action == 'end_chapter':
            print('ended', self.current)
            print(self.current.text)
            self.current = None

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        if self.data_stack:
            self.data_stack[-1] += c


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


def parse_html_file(path):
    parser = MyHTMLParser(strict=True)
    with open(path, 'r') as f:
        parser.feed(f.read())
        parser.close()


def main(script, path='', command=''):
    if not os.path.isfile(path):
        print("")
        sys.exit(2)

    parse_html_file(path)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
