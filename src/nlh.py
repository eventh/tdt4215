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
        return self.to_json()

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
        elif self.chapters:
            if tag == 'div' and class_ == 'revidert':
                action = 'store_revidert'
            elif tag == 'div' and class_ == 'def':
                self.actions[-1][1].append('\n')
            elif tag == 'div' and class_ == 'tone':
                self.actions[-1][1].append('\n')
            elif tag == 'p' and class_ == 'defa':
                self.actions[-1][1].append(': ')
            elif tag == 'h3':
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


def main(script, path='', command='parse'):
    if not os.path.isfile(path):
        print("")
        sys.exit(2)

    folder, filename = os.path.split(path)
    filename, ext = os.path.splitext(filename)

    if command == 'parse':
        parse_html_file(path)
        dump_chapters_to_json(filename)
    elif command.startswith('pre'):
        preprocess_html_file(path, path + 'l')

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
