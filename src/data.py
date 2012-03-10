#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys
import os
import time
import json
from collections import OrderedDict

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED

from tasks import ANALYZER


def _read_stopwords():
    """Read in and return stop-words from file."""
    with open('etc/stoppord.txt', 'r') as f:
        return set(i.strip() for i in f.readlines() if i.strip())


class BaseData:

    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.code

    def to_json(self):
        pass

    def to_index(self):
        pass

    @classmethod
    def from_json(cls, values):
        pass

    @classmethod
    def populate(cls):
        """Populate objects from JSON file."""
        with open(cls._JSON, 'r') as f:
            return [cls.from_json(i) for i in json.load(f)]


class ATC(BaseData):
    """Anatomical Therapeutic Chemical classification system of drugs.

    The drugs are divided into fourteen main groups (1st level), with
    pharmacological/therapeutic subgroups (2nd level). The 3rd and 4th levels
    are chemical/pharmacological/therapeutic subgroups and the 5th level is
    the chemical substance.
    """

    ALL = []  # All ATC objects
    _NAME = 'atc'  # Index name
    _JSON = 'etc/atcname.json'  # JSON file

    # Schema for storing and indexing ATC codes in whoosh database
    SCHEMA = Schema(code=ID(stored=True), name=TEXT(stored=True))

    def __init__(self, code, name):
        """Create a new ATC object."""
        self.code = code
        self.name = name
        ATC.ALL.append(self)

    def __str__(self):
        """Present the object as a string."""
        return '%s: %s' % (self.code, self.name)

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        obj['code'] = self.code
        obj['name'] = self.name
        return obj

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return self.to_json()

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        return cls(values['code'], values['name'])


class ICD(BaseData):
    """Classification of Diseases and Health Problems.

    The International Statistical Classification of Diseases and Related
    Health Problems, 10th Revision (known as "ICD-10") is a medical
    classification list for the coding of diseases, signs and symptoms,
    abnormal findings, complaints, social circumstances, and external
    causes of injury or diseases.
    """

    ALL = {}  # All ICD10 objects
    _NAME = 'icd'  # Index name
    _JSON = 'etc/icd10no.json'  # JSON file

    # Schema for storing and indexing ICD10 codes in whoosh database
    SCHEMA = Schema(code=ID(stored=True), short=ID(stored=True),
                    label=TEXT(stored=True), type=TEXT, icpc2_code=ID,
                    icpc2_label=TEXT, synonyms=TEXT, terms=TEXT,
                    inclusions=TEXT, exclusions=TEXT, description=TEXT)

    _fields = ('code', 'short', 'label', 'type',
               'icpc2_code', 'icpc2_label', 'parent')
    _lists = ('inclusions', 'exclusions', 'terms', 'synonyms')

    def __init__(self):
        """Create a new ICD10 object."""
        for i in self._lists:
            setattr(self, i, '')
        for i in self._fields:
            setattr(self, i, None)

    @property
    def description(self):
        label = self.label
        if self.icpc2_label:
            label += self.icpc2_label
        return '\n'.join((label, self.terms, self.synonyms, self.inclusions))

    def __str__(self):
        """Present the object as a string."""
        return '%s: %s' % (self.short, self.label)

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        for var in self._fields + self._lists:
            if getattr(self, var):
                obj[var] = getattr(self, var)
        return obj

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        obj = self.to_json()
        obj['description'] = self.description
        if 'parent' in obj:
            del obj['parent']
        return obj

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        obj = cls()
        for i in cls._lists + cls._fields:
            if i in values:
                setattr(obj, i, values[i])
        ICD.ALL[values['short']] = obj
        return obj


# Inverse Document and Term Frequency Weight functions
def _idf(N, n):
    return log(N / n)  # Inverse frequency
def _idf_smooth(N, n):
    return log(1 + (N / n))  # Inverse frequency smooth
def _idf_prob(N, n):
    return log((N - n) / n)  # Probabilistic inverse frequency
def _tf_log_norm(frequency):
    return 1 + log(frequency)  # Log normalization


class Medicin(BaseData):

    ALL = {}
    _NAME = 'med'
    SCHEMA = Schema(code=ID(stored=True, unique=True),
                    text=TEXT(vector=True, analyzer=ANALYZER))

    def __init__(self, code, text):
        Medicin.ALL[code] = self
        self.code = code
        self.text = text
        self.vector = None

    def to_index(self):
        return {'code': self.code, 'text': self.text}

    def to_json(self):
        return {'code': self.code, 'text': self.text, 'vector': self.vector}

    @classmethod
    def create_vectors(cls):
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=cls.NAME)
        with ix.searcher() as searcher:
            def idf(term):
                N = searcher.doc_count()
                n = searcher.doc_frequency('text', term)
                return _idf(N, n)

            for doc_num in searcher.document_numbers():
                obj = cls.ALL[searcher.stored_fields(doc_num)['code']]
                obj.vector = {t: _tf_log_norm(w) * idf(t) for t, w in
                              searcher.vector_as('weight', doc_num, 'text')}

        print("Created vectors in %.2f seconds" % (time.time() - now))

    @classmethod
    def populate(cls, cases, chapters):
        for name, lines in cases.items():
            PatientCase(name, '\n'.join(lines))
        for chapter in chapters:
            if chapter.text:
                Therapy(chapter)


class PatientCase(Medicin):

    ALL = {}
    _NAME = 'case'
    _JSON = 'etc/cases.json'  # JSON file

    def __init__(self, code, text):
        PatientCase.ALL[code] = self
        super().__init__(code, text)

    def to_json(self):
        obj = OrderedDict()
        obj['code'] = self.code
        obj['lines'] = self.text.split('\n')
        return obj


class Therapy(Medicin):
    """A (sub)*chapter in norsk legemiddelhandbok."""

    ALL = {}  # All Chapter objects
    _NAME = 'terapi'  # Index name
    _JSON = 'etc/therapy.json'  # JSON file

    # Schema for storing and indexing chapters in whoosh database
    SCHEMA = Schema(code=ID(stored=True), title=TEXT(stored=True), text=TEXT)

    def __init__(self, code=None, title=None, text=''):
        """Create a new chapter representing a part of NLH."""
        if code is not None:
            Therapy.ALL[code] = self
        self.code = code
        self.title = title
        self.text = text
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


def main(script, path='', command=''):
    """Convert data files to JSON, or load data into index.

    Usage: python3 codes.py <path> <store|clean>
    """
    if not path:
        print("Need to supply a path to a file to parse")
        print("Usage: python3 codes.py <path> <command>")
        sys.exit(2)

    # Split path in folder, filename, file extension
    folder, filename = os.path.split(path)
    filename, ext = os.path.splitext(filename)

    now = time.time()

    # Load from JSON
    if ext == '.json':
        with open(path, 'r') as f:
            json_objects = json.load(f)

        if filename.startswith('atcname'):
            cls = ATC  # Hack
        else:
            cls = ICD

        objects = [cls.from_json(i) for i in json_objects]
        print("Loaded %s objects from %s in %.2f seconds" % (
                len(objects), path, time.time() - now))

    if not command or not objects:
        sys.exit(None)
    cls = objects[0].__class__

    # Store objects in index
    if command == 'store':
        create_index(cls)
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=cls.NAME)
        with ix.writer() as writer:
            for obj in objects:
                writer.add_document(**obj.to_index())
        print("Stored %s %s objects in index in %.2f seconds" % (
                len(objects), cls.__name__, time.time() - now))

    # Empty index
    elif command in ('clean', 'clear'):
        create_index(cls)
        ix = create_in(INDEX_DIR, schema=cls.SCHEMA, indexname=cls.NAME)
        print("Emptied %s index" % cls.__name__)

    # Unknown command
    else:
        print("Unknown command '%s'" % command)
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
