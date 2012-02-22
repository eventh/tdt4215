#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for converting data to JSON, and for loading it into whoosh index.

Example usage:
To convert ICD XML file to JSON run the following command:
    'python data.py ../data/icd10no.xml'

To insert ATC into whoosh index from JSON run the following command:
    'python data.py etc/atcname.json store'
"""
import sys
import os
import json
import time
import xml.etree.ElementTree as ET

from whoosh.index import create_in, open_dir, exists_in

from schemas import ATC_SCHEMA, ICD10_SCHEMA, INDEX_DIR


class ATC(object):
    """Anatomical Therapeutic Chemical classification system of drugs.

    The drugs are divided into fourteen main groups (1st level), with
    pharmacological/therapeutic subgroups (2nd level). The 3rd and 4th levels
    are chemical/pharmacological/therapeutic subgroups and the 5th level is
    the chemical substance.
    """

    SCHEMA = ATC_SCHEMA
    NAME = 'atc'

    def __init__(self, code, name):
        """Create a new ATC object."""
        self.code = code
        self.name = name

    def __str__(self):
        """Present the object as a string."""
        output = '%s: %s' % (self.code, self.name)
        return output.encode('ascii', 'ignore')

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        return {'code': self.code, 'name': self.name}

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return self.to_json()

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        return cls(values['code'], values['name'])


class ICD10(object):
    """Classification of Diseases and Health Problems.

    The International Statistical Classification of Diseases and Related
    Health Problems, 10th Revision (known as "ICD-10") is a medical
    classification list for the coding of diseases, signs and symptoms,
    abnormal findings, complaints, social circumstances, and external
    causes of injury or diseases.
    """

    SCHEMA = ICD10_SCHEMA
    NAME = 'icd10'

    lists = ('inclusions', 'exclusions', 'terms', 'synonyms')
    fields = ('short', 'code', 'label', 'formatted', 'type', 'icpc2_label')

    def __init__(self):
        """Create a new ICD10 object."""
        for i in self.lists:
            setattr(self, i, u'')
        for i in self.fields:
            setattr(self, i, None)

    def __str__(self):
        """Present the object as a string."""
        output = '%s: %s' % (self.short, self.label)
        return output.encode('ascii', 'ignore')

    def to_json(self):
        """Create a dictionary with object values for JSON dump."""
        return {i: getattr(self, i)
                    for i in self.lists + self.fields if getattr(self, i)}

    def to_index(self):
        """Create a dictionary with values to store in whoosh index."""
        return self.to_json()

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        obj = cls()
        for i in cls.lists + cls.fields:
            if i in values:
                setattr(obj, i, values[i])
        return obj


def parse_xml_file(path):
    """Parse an XML file which contains ICD10 codes.

    Returns a list of ICD10 objects which are populated from the file.
    """
    # Tags found in XML file
    ignore_tags = ('subClassOf', 'umls_tui', 'umls_conceptId', 'umls_atomId')
    list_mapping = {'underterm': 'terms', 'synonym': 'synonyms',
                    'inclusion': 'inclusions', 'exclusion': 'exclusions'}
    tag_mapping = {'label': 'label', 'code_compacted': 'short',
                   'code_formatted': 'formatted', 'umls_semanticType': 'type',
                   'icpc2_label': 'icpc2_label', 'icpc2_code': 'code'}

    # Parse XML file
    tree = ET.parse(path)
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
                    value += child.text.strip() + u'\n'
                    setattr(obj, list_mapping[tag], value)
            elif tag in tag_mapping:
                setattr(obj, tag_mapping[tag], child.text)
            elif tag not in ignore_tags:
                print "Unknown tag", tag, ":", child.text, child.tail

        if obj.short and obj.label:
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
                code = u''.join(code.split(','))
                name = rest.split("'")[1]
                name = unicode(name, errors='ignore')  # TODO
                objects.append(ATC(code, name))
    return objects


def main(script, path='', command=''):
    """Convert data files to JSON, or load data into index.

    Usage: python data.py <path> <store|clean>
    """
    if not path:
        print "Need to supply a path to a file to parse"
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
        print "Dumped %s objects to %s.json in %.2f seconds" % (
                len(objects), filename, time.time() - now)

    # Load from JSON
    elif ext == '.json':
        with open(path, 'r') as f:
            json_objects = json.load(f)

        if filename == 'atcname':
            cls = ATC  # Hack
        else:
            cls = ICD10

        objects = [cls.from_json(i) for i in json_objects]
        print "Loaded %s objects from %s in %.2f seconds" % (
                len(objects), path, time.time() - now)

    else:
        print "Unknown file, must be JSON, XML or PL filetype: %s" % path
        sys.exit(2)

    if not command or not objects:
        sys.exit(None)
    cls = objects[0].__class__

    # Create index if necesseary
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    if not exists_in(INDEX_DIR, indexname=cls.NAME):
        ix = create_in(INDEX_DIR, schema=cls.SCHEMA, indexname=cls.NAME)
        print "Created %s index" % cls.__name__

    # Store objects in index
    if command == 'store':
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=cls.NAME)
        writer = ix.writer()
        for obj in objects:
            writer.add_document(**obj.to_index())
        writer.commit()
        print "Stored %s %s objects in index in %.2f seconds" % (
                len(objects), cls.__name__, time.time() - now)

    # Empty index
    elif command == 'clean':
        ix = create_in(INDEX_DIR, schema=cls.SCHEMA, indexname=cls.NAME)
        print "Emptied %s index" % cls.__name__

    # Unknown command
    elif command:
        print "Unknown command '%s'" % command
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
