#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing html documents from 'norsk legemiddelhåndbok'.
"""
import os
import sys
import time
import string
import json
from collections import OrderedDict
from html.parser import HTMLParser


class Chapter:

    ALL = []

    def __init__(self, type):
        Chapter.ALL.append(self)
        self.type = type

        self.code = None
        self.title = None
        self.revidert = None
        self.text = ''
        self.links = []

    def __str__(self):
        """Represent the object as a string."""
        return '%s: %s' % (self.code, self.title)

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        obj['code'] = self.code
        obj['title'] = self.title
        obj['text'] = [i for i in self.text.split('\n') if i]
        obj['links'] = [i.text for i in self.links]
        return obj

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return {'code': self.code, 'title': self.title, 'text': self.text}

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        #return cls(values['code'], values['name'])
        pass


class Link:
    def __init__(self, href):
        self.href = href
        self.text = ''

    def __str__(self):
        return 'Link %s (%s)' % (self.text, self.href)


class NLHParser(HTMLParser):
    """Parser for  Norwegian Legemiddelhandboka HTML pages."""

    _tags = ('strong', 'div', 'p', 'h2', 'h3', 'h4', 'h5', 'a')

    def __init__(self, *args, **vargs):
        super().__init__(*args, **vargs)

        self.actions = []  # Stack for actions to perform
        self.chapters = []  # Stack for chapters

    def _get_attr(self, attrs, key):
        """Get an attribute value from set of 'attrs'."""
        for tmp, value in attrs:
            if key == tmp:
                return value
        return None

    def _split_title(self, title):
        """Split a chapter into code and title."""
        i = 2  # Code can start with *T
        while i < len(title):
            if title[i] not in string.digits and title[i] != '.':
                break
            i += 1
        return title[:i], title[i:]

    def handle_starttag(self, tag, attrs):
        """Handle the start of a HTML tag."""
        class_ = self._get_attr(attrs, 'class')
        action = 'pop'

        if tag == 'div' and class_ == 'seksjon2':
            self.chapters.append(Chapter('chapter'))
            action = 'end_chapter'
        elif tag == 'div' and class_ == 'seksjon3':
            self.chapters.append(Chapter('subsubchapter'))
            action = 'end_chapter'
        elif self.chapters:
            if tag == 'div' and class_ == 'revidert':
                action = 'store_revidert'
            elif tag == 'div' and class_ == 'def':
                self.actions[-1][1].append('\n')
            elif tag == 'div' and class_ == 'tone':
                self.actions[-1][1].append('\n')
            elif tag == 'p' and class_ == 'defa':
                self.actions[-1][1].append(': ')
            elif tag in ('h3', 'h2'):
                action = 'store_title'
            elif tag == 'a':
                link = Link(self._get_attr(attrs, 'href'))
                self.chapters[-1].links.append(link)
                action = 'store_link'

        self.actions.append([action, []])

    def handle_data(self, data):
        """Handle text."""
        if self.actions:
            self.actions[-1][1].append(data.strip())

    def handle_endtag(self, tag):
        """Handle the end of an HTML tag."""
        if not self.actions:
            return

        action, data = self.actions.pop()
        data = ' '.join(i for i in ''.join(data).split(' ') if i)

        obj = self.chapters[-1] if self.chapters else None

        if action == 'store_title':
            obj.code, obj.title = self._split_title(data)
        elif action == 'store_revidert':
            obj.revidert = data
        elif action == 'store_link':
            obj.links[-1].text = data
            self.actions[-1][1].append(data)
        elif action == 'end_chapter':
            obj.text += data
            self.chapters.pop()
            print(obj, obj.text)
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
    """Parse Norwegian Legemiddelhandboka HTML page 'path'."""
    now = time.time()
    parser = NLHParser(strict=True)
    with open(path, 'r') as f:
        parser.feed(f.read())
        parser.close()
    print("Parsed '%s' in %.2f seconds" % (path, time.time() - now))


def dump_chapters_to_json(filename):
    """Dump all parsed Chapter objects to JSON."""
    now = time.time()
    with open("%s.json" % filename, 'w') as f:
        json.dump([i.to_json() for i in Chapter.ALL], f, indent=4)
    print("Dumped %s objects to %s.json in %.2f seconds" % (
        len(Chapter.ALL), filename, time.time() - now))


def main(script, folder_or_path='', command='parse'):
    if not os.path.exists(folder_or_path):
        print("Error: must be given a valid path '%s'" % folder_or_path)
        print("Usage: python3 nlh.py <path> <parse|preprocess>")
        sys.exit(2)

    # Accept path to either a folder or a file
    paths = []
    if not os.path.isdir(folder_or_path):
        paths.append(folder_or_path)
    else:
        for path in os.listdir(folder_or_path):
            full_path = os.path.normpath(os.path.join(folder_or_path, path))
            if not os.path.isdir(full_path):
                paths.append(full_path)

    # Parse HTML files to find objects
    if command == 'parse':
        for path in paths:
            folder, filename = os.path.split(path)
            parse_html_file(path)
            dump_chapters_to_json(os.path.splitext(filename)[0])

    # Preprocess HTML files to make them easier to parse
    elif command.startswith('pre'):
        now = time.time()
        for path in paths:
            if os.path.splitext(path)[1] == '.htm':
                preprocess_html_file(path, path + 'l')
        print("Preprocessed %i .htm files in %.2f seconds" % (
                len(paths), time.time() - now))

    else:
        print("Unknown command '%s', must be either parse or pre" % command)
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
