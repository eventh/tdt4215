#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing html documents from 'norsk legemiddelhandbok'.
"""
import os
import sys
import time
import string
import json
from collections import OrderedDict
from html.parser import HTMLParser

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.index import open_dir, create_in

from codes import INDEX_DIR, create_index


class Chapter:
    """A (sub)*chapter in norsk legemiddelhandbok."""

    # Schema for storing and indexing chapters in whoosh database
    SCHEMA = Schema(code=ID(stored=True), title=TEXT(stored=True), text=TEXT)

    NAME = 'terapi'  # Index name
    ALL = []  # All Chapter objects

    def __init__(self):
        """Create a new chapter representing a part of NLH."""
        Chapter.ALL.append(self)
        self.code = None
        self.title = None
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
        obj['links'] = self.links
        return obj

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return {'code': self.code, 'title': self.title, 'text': self.text}

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        obj = cls()
        obj.code = values['code']
        obj.title = values['title']
        obj.text = '\n'.join(values['text'])
        obj.links = values['links']
        return obj


class NLHParser(HTMLParser):
    """Parser for  Norwegian Legemiddelhandboka HTML pages."""

    _section_classes = ('seksjon2', 'seksjon3', 'seksjon4', 'seksjon8')
    _ignore_tags = ('br', 'input', 'img', 'tr', 'hr')
    _title_tags = ('h1', 'h2', 'h3', 'h4', 'h5')

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

    def _force_end_chapter(self):
        """Force end of a chapter when a new chapter starts."""
        while self.actions:
            if self.actions[-1][0] == 'end_chapter':
                self.handle_endtag()
                break
            self.handle_endtag()

    def handle_starttag(self, tag, attrs):
        """Handle the start of a HTML tag."""
        if tag in self._ignore_tags:
            return  # Has optional end-tag

        action = 'pop'
        class_ = self._get_attr(attrs, 'class')

        # Start a new chapter
        if ((tag == 'section' and self._get_attr(attrs, 'id') == 'page')
                or (tag == 'div' and class_ in self._section_classes)):
            self.chapters.append(Chapter())
            action = 'end_chapter'

        elif self.chapters:
            if tag in self._title_tags and self.chapters[-1].code is None:
                action = 'store_title'
            elif tag == 'div' and class_ in ('def', 'tone'):
                self.actions[-1][1].append('\n')
                if class_ == 'tone':
                    action = 'discard'
            elif tag == 'div' and class_ in ('revidert', 'forfatter'):
                action = 'discard'
            elif tag == 'a':
                action = 'store_link'
            elif tag == 'h5':
                action = 'add_colon'

        self.actions.append([action, []])

    def handle_data(self, data):
        """Handle text."""
        if self.actions:
            self.actions[-1][1].append(data.strip())

    def handle_endtag(self, tag=''):
        """Handle the end of an HTML tag."""
        if tag in self._ignore_tags or not self.actions:
            return

        # Broken HTML means that chapters might not be ended
        if tag == 'html':
            while self.chapters:
                self._force_end_chapter()
            return

        action, data = self.actions.pop()
        data = ' '.join(i for i in ''.join(data).split(' ') if i)

        obj = self.chapters[-1] if self.chapters else None

        if action == 'add_colon':
            data += ': '
        if action == 'discard':
            pass
        elif action == 'store_title':
            obj.code, obj.title = self._split_title(data)
        elif action == 'store_link':
            obj.links.append(data)
            self.actions[-1][1].append(' %s ' % data)
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

            # Remove most of <head> and <footer>
            lines = lines[:3] + lines[4:5] + lines[28:-10] + lines[-4:]

            # Save lines to output file
            f2.write('\n'.join(lines))


def parse_html_file(path):
    """Parse Norwegian Legemiddelhandboka HTML page 'path'."""
    parser = NLHParser(strict=True)
    with open(path, 'r') as f:
        parser.feed(f.read())
        parser.close()


def dump_chapters_to_json(filename):
    """Dump all parsed Chapter objects to JSON."""
    now = time.time()
    objects = [i.to_json() for i in Chapter.ALL if i.text]
    with open("%s.json" % filename, 'w') as f:
        json.dump(objects, f, indent=4)
    print("Dumped %s objects to %s.json in %.2f seconds" % (
        len(objects), filename, time.time() - now))


def load_objects_from_json(path):
    """Load chapter objects from JSON file 'path'."""
    now = time.time()
    with open(path, 'r') as f:
        json_objects = json.load(f)
    objects = [Chapter.from_json(i) for i in json_objects]
    print("Loaded %s objects from %s in %.2f seconds" % (
        len(objects), path, time.time() - now))


def main(script, folder_or_path='', command=''):
    """Handle chapters from norsk legemiddelhandbok.

    'folder_or_path' is either a folder or a html or json file.
    'command' is optionally one of parse, preprocess, store, clean.
    Usage: python3 nlh.py <path_or_folder> [parse|preprocess|store|clean]
    """
    if not os.path.exists(folder_or_path):
        print("Error: must be given a valid path '%s'" % folder_or_path)
        print("Usage: python3 nlh.py <path> [parse|preprocess|store|clean]")
        sys.exit(2)

    # Parse JSON file with Chapter objects
    if folder_or_path[-5:] == '.json':
        load_objects_from_json(folder_or_path)

    #lines = sum(i.text.count('\n') + 1 for i in Chapter.ALL if i.text)
    #print(lines)

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
    now = time.time()
    if command == 'parse':
        for path in paths:
            folder, filename = os.path.split(path)
            if os.path.splitext(filename)[1] == '.html':
                parse_html_file(path)
        print("Parsed '%s', %i chapters in %.2f seconds" % (
                folder_or_path, len(Chapter.ALL), time.time() - now))
        dump_chapters_to_json('terapi')

    # Preprocess HTML files to make them easier to parse
    elif command.startswith('pre'):
        for path in paths:
            if os.path.splitext(path)[1] == '.htm':
                preprocess_html_file(path, path + 'l')
        print("Preprocessed %i .htm files in %.2f seconds" % (
                len(paths), time.time() - now))

    # Store objects in index
    elif command == 'store':
        create_index(Chapter)
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=Chapter.NAME)
        objects = [i for i in Chapter.ALL if i.text]
        with ix.writer() as writer:
            for obj in objects:
                    writer.add_document(**obj.to_index())
        print("Stored %s terapi chapter objects in index in %.2f seconds" % (
                len(objects), time.time() - now))

    # Empty index
    elif command in ('clean', 'clear'):
        create_index(Chapter)
        ix = create_in(INDEX_DIR, schema=Chapter.SCHEMA, indexname=Chapter.NAME)
        print("Emptied %s index" % Chapter.__name__)

    elif command:
        print("Unknown command: %s" % command)
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
