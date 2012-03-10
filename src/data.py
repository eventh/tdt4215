#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
import sys
import os
import time
import json
from collections import OrderedDict


class BaseData:

    def __init__(self, code, title=''):
        self.code = code
        self.title = title

    def __str__(self):
        """Represent the object as a string."""
        if self.title:
            return '%s: %s' % (self.code, self.title)
        else:
            return self.code

    def to_json(self):
        raise NotImplementedError("%s must implement this!" % self)

    def to_index(self):
        raise NotImplementedError("%s must implement this!" % self)

    @classmethod
    def from_json(cls, values):
        raise NotImplementedError("%s must implement this!" % cls.__name__)

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

    def __init__(self, code, title):
        """Create a new ATC object."""
        ATC.ALL.append(self)
        super().__init__(code, title)

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return self.to_json()

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        obj['code'] = self.code
        obj['title'] = self.title
        return obj

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        return cls(values['code'], values['title'])


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

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        obj = self.to_json()
        obj['description'] = self.description
        if 'parent' in obj:
            del obj['parent']
        return obj

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        for var in self._fields + self._lists:
            if getattr(self, var):
                obj[var] = getattr(self, var)
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
    _NAME = 'medicin'

    def __init__(self, code, text):
        Medicin.ALL[code] = self
        self.code = code
        self.text = text
        self.vector = None

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


class PatientCase(Medicin):

    ALL = {}  # All PatientCase objects
    _JSON = 'etc/cases.json'  # JSON file

    def __init__(self, code, text):
        """Create a new PatientCase object."""
        PatientCase.ALL[code] = self
        super().__init__(code, text)

    def to_index(self):
        return {'code': self.code, 'text': self.text}

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        obj['code'] = self.code
        obj['lines'] = self.text.split('\n')
        return obj

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        return cls(values['code'], '\n'.join(values['lines']))


class Therapy(Medicin):
    """A (sub)*chapter in norsk legemiddelhandbok."""

    ALL = {}  # All Therapy objects
    _NAME = 'therapy'  # Index name
    _JSON = 'etc/therapy.json'  # JSON file

    def __init__(self, code=None, title=None, text=''):
        """Create a new therapy chapter representing a part of NLH."""
        if code is not None:
            super().__init__(code, text)
            Therapy.ALL[code] = self
        self.code = code
        self.title = title
        self.text = text
        self.links = []

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return {'code': self.code, 'title': self.title, 'text': self.text}

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        obj = OrderedDict()
        obj['code'] = self.code
        obj['title'] = self.title
        obj['text'] = [i for i in self.text.split('\n') if i]
        obj['links'] = self.links
        return obj

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        obj = cls(values['code'], values['title'], '\n'.join(values['text']))
        obj.links = values['links']
        return obj


def get_stopwords():
    """Read in and return stop-words from file."""
    with open('etc/stoppord.txt', 'r') as f:
        return set(i.strip() for i in f.readlines() if i.strip())


def populate_all():
    for cls in (ATC, ICD, PatientCase, Therapy):
        cls.populate()
        if not cls.ALL:
            print("Failed to populate %s from %s" % (cls.__name__, cls._JSON))
            sys.exit(1)


def main(script=None):
    """Test if objects can be populated and indices contains data."""
    # Check if json files exists
    for cls in (ATC, ICD, PatientCase, Therapy):
        if not os.path.isfile(cls._JSON):
            print("Missing json file %s, use 'parse.py' to fix" % cls._JSON)
            sys.exit(1)

    # Load objects from JSON files
    now = time.time()
    populate_all()
    print("Populated ATC %i, ICD %i, Cases %i, Therapy %i in %.2f seconds" % (
            len(ATC.ALL), len(ICD.ALL), len(PatientCase.ALL),
            len(Therapy.ALL), time.time() - now))

    # Check if indices exists and contains documents
    import index
    empty = index.get_empty_indices()
    if empty:
        print("Empty indices '%s', run 'python3 index.py build' to fix" %
                ', '.join(i.__name__ for i in empty))
        sys.exit(1)

    print("All A-OK")
    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
