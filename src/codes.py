#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A module for converting data to JSON, and for loading it into whoosh index.

Example usage:
To convert ICD XML file to JSON run the following command:
    'python3 codes.py ../data/icd10no.xml'

To insert ATC into whoosh index from JSON run the following command:
    'python3 codes.py etc/atcname.json store'
"""
import sys
import os
import time
import json
from collections import OrderedDict
from xml.etree import ElementTree

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.index import create_in, open_dir, exists_in


# Settings
INDEX_DIR = 'indexdir'


class ATC:
    """Anatomical Therapeutic Chemical classification system of drugs.

    The drugs are divided into fourteen main groups (1st level), with
    pharmacological/therapeutic subgroups (2nd level). The 3rd and 4th levels
    are chemical/pharmacological/therapeutic subgroups and the 5th level is
    the chemical substance.
    """

    # Schema for storing and indexing ATC codes in whoosh database
    SCHEMA = Schema(code=ID(stored=True), name=TEXT(stored=True))

    NAME = 'atc'  # Index name
    ALL = {}  # All ATC objects

    def __init__(self, code, name):
        """Create a new ATC object."""
        self.code = code
        self.name = name
        ATC.ALL[code] = self

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


class ICD10:
    """Classification of Diseases and Health Problems.

    The International Statistical Classification of Diseases and Related
    Health Problems, 10th Revision (known as "ICD-10") is a medical
    classification list for the coding of diseases, signs and symptoms,
    abnormal findings, complaints, social circumstances, and external
    causes of injury or diseases.
    """

    # Schema for storing and indexing ICD10 codes in whoosh database
    ICD10_SCHEMA = Schema(code=ID(stored=True), short=ID(stored=True),
                          label=TEXT(stored=True), type=TEXT, icpc2_code=ID,
                          icpc2_label=TEXT, synonyms=TEXT, terms=TEXT,
                          inclusions=TEXT, exclusions=TEXT, description=TEXT)

    NAME = 'icd10'  # Index name
    ALL = {}  # All ICD10 objects

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
        ICD10.ALL[values['short']] = obj
        return obj


def is_indices_empty():
    """Check if indexes exists and contains documents."""
    if not os.path.isdir(INDEX_DIR):
        return True

    index_names = (ATC.NAME, ICD10.NAME)
    for name in index_names:
        if not exists_in(INDEX_DIR, indexname=name):
            return True
        ix = open_dir(INDEX_DIR, indexname=name)
        if ix.doc_count() < 1:
            return True

    return False


def populate_data_from_json():
    """Populate ICD10 and ATC objects from JSON files."""
    files = {'etc/icd10no.json': ICD10, 'etc/atcname.json': ATC}
    for path in list(files.keys()) + [INDEX_DIR]:
        if not os.path.exists(path):
            raise IOError("Missing file or index: %s" % path)
    for path, cls in files.items():
        with open(path, 'r') as f:
            json_objects = json.load(f)
        objects = [cls.from_json(i) for i in json_objects]


def parse_xml_file(path):
    """Parse an XML file which contains ICD10 codes.

    Returns a list of ICD10 objects which are populated from the file.
    """
    # Tags found in XML file
    ignore_tags = ('umls_tui', 'umls_conceptId', 'umls_atomId')
    list_mapping = {'underterm': 'terms', 'synonym': 'synonyms',
                    'inclusion': 'inclusions', 'exclusion': 'exclusions'}
    tag_mapping = {'label': 'label', 'code_compacted': 'short',
                   'code_formatted': 'code', 'umls_semanticType': 'type',
                   'icpc2_label': 'icpc2_label', 'icpc2_code': 'icpc2_code'}

    # Parse XML file
    tree = ElementTree.parse(path)
    nodes = tree.getroot().findall('{http://www.w3.org/2002/07/owl#}Class')

    # Traverse nodes to create and populate ICD10 objects
    objects = []
    for node in nodes:
        obj = ICD10()
        for child in node:
            tag = child.tag.split('}')[1]

            if tag in list_mapping:
                if child.text:
                    value = getattr(obj, list_mapping[tag])
                    if value:
                        value += '\n'
                    value += child.text.strip().replace('<i>', '').replace('</i>', '')
                    setattr(obj, list_mapping[tag], value)
            elif tag in tag_mapping:
                setattr(obj, tag_mapping[tag], child.text)
            elif tag == 'subClassOf':
                value, = list(child.attrib.values())
                obj.parent = value.split('#')[1][:-1]
            elif tag not in ignore_tags:
                print("Unknown tag %s, %s, %s" % (tag, child.text, child.tail))

        if obj.short and obj.label:
            if not obj.code:
                obj.code = obj.short  # Hack to simplify handling results
            objects.append(obj)
        else:
            del obj
    return objects


def parse_pl_file(path):
    """Parse a Prolog fact file which contains ATC codes.

    Returns a list of ATC objects which are populated from the file.
    """
    objects = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('atcname( [') and line.endswith(').\n'):
                code, rest = line[10:-3].split(']', 1)
                code = ''.join(code.split(','))
                name = rest.split("'")[1]
                objects.append(ATC(code, name))
    return objects


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

    # Convert to JSON
    if ext in ('.pl', '.xml'):
        if ext == '.pl':
            objects = parse_pl_file(path)
        else:
            objects = parse_xml_file(path)

        with open("%s.json" % filename, 'w') as f:
            json.dump([i.to_json() for i in objects], f, indent=4)
        print("Dumped %s objects to %s.json in %.2f seconds" % (
                len(objects), filename, time.time() - now))

    # Load from JSON
    elif ext == '.json':
        with open(path, 'r') as f:
            json_objects = json.load(f)

        if filename.startswith('atcname'):
            cls = ATC  # Hack
        else:
            cls = ICD10

        objects = [cls.from_json(i) for i in json_objects]
        print("Loaded %s objects from %s in %.2f seconds" % (
                len(objects), path, time.time() - now))

    else:
        print("Unknown file '%s', must be JSON, XML or PL filetype" % path)
        sys.exit(2)

    if not command or not objects:
        sys.exit(None)
    cls = objects[0].__class__

    # Create index if necessary
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    if not exists_in(INDEX_DIR, indexname=cls.NAME):
        ix = create_in(INDEX_DIR, schema=cls.SCHEMA, indexname=cls.NAME)
        print("Created %s index" % cls.__name__)

    # Store objects in index
    if command == 'store':
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=cls.NAME)
        with ix.writer() as writer:
            #writer = ix.writer()
            for obj in objects:
                writer.add_document(**obj.to_index())
        #writer.commit()
        print("Stored %s %s objects in index in %.2f seconds" % (
                len(objects), cls.__name__, time.time() - now))

    # Empty index
    elif command in ('clean', 'clear'):
        ix = create_in(INDEX_DIR, schema=cls.SCHEMA, indexname=cls.NAME)
        print("Emptied %s index" % cls.__name__)

    # Unknown command
    elif command:
        print("Unknown command '%s'" % command)
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
