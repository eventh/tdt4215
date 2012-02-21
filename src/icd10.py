#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for loading ICD10 objects from either XML or JSON file into index.
"""
import sys
import os
import json
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from whoosh.index import create_in, open_dir

from schemas import ICD10_SCHEMA, INDEX_DIR



class ICD10(object):

    lists = ('inclusions', 'exclusions', 'terms', 'synonyms')
    fields = ('short', 'code', 'label', 'formatted', 'type', 'icpc2_label')

    def __init__(self):
        """Create a new ICD10 object."""
        for i in self.lists:
            setattr(self, i, [])
        for i in self.fields:
            setattr(self, i, None)

    def __str__(self):
        output = "%s: %s" % (self.short, self.label)
        return output.encode('ascii', 'ignore')

    def to_json(self):
        return {i: getattr(self, i) for i in self.lists + self.fields}

    def get_whoosh_args(self):
        return {i: getattr(self, i) for i in self.lists + self.fields}

    @classmethod
    def from_json(cls, values):
        obj = cls()
        for i in cls.lists + cls.fields:
            setattr(obj, i, values[i])
        return obj


def parse_xml_file(path):
    """Parse an XML file which contains ICD10 codes.

    Returns a list of ICD10 objects which are populated from the file.
    """
    ignore_tags = ('subClassOf', 'umls_tui', 'umls_conceptId', 'umls_atomId')

    # Parse XML file
    tree = ET.parse(path)
    nodes = tree.getroot().findall('{http://www.w3.org/2002/07/owl#}Class')

    # Traverse nodes to create and populate ICD10 objects
    objects = []
    for node in nodes:
        obj = ICD10()
        for child in node:
            tag = child.tag.split('}')[1]

            if tag in ignore_tags:
                pass
            elif tag == 'label':
                obj.label = child.text
            elif tag == 'code_compacted':
                obj.short = child.text
            elif tag == 'code_formatted':
                obj.formatted = child.text
            elif tag == 'umls_semanticType':
                obj.type = child.text
            elif tag == 'icpc2_code':
                obj.code = child.text
            elif tag == 'icpc2_label':
                obj.icpc2_label = child.text
            elif tag == 'underterm':
                if child.text:
                    obj.terms.append(child.text.strip())
            elif tag == 'synonym':
                if child.text:
                    obj.synonyms.append(child.text.strip())
            elif tag == 'inclusion':
                if child.text:
                    obj.inclusions.append(child.text.strip())
            elif tag == 'exclusion':
                if child.text:
                    obj.exclusions.append(child.text.strip())
            else:
                print "Unknown tag", tag, ":", child.text, child.tail

        if obj.short and obj.label:
            objects.append(obj)
        else:
            del obj

    return objects


def main(script, path='', command=''):
    """Read ICD10 objects from file and load into index.

    Usage: python icd10.py <input file> <store|clean>
    Path is the path to the input file, either JSON or XML.
    Command is either 'store' into database or 'clean' database.
    """
    if not path:
        print "Need to supply icd10 file or json file to parse"
        sys.exit(2)

    # Split path in folder, filename, file extension
    folder, filename = os.path.split(path)
    filename, ext = os.path.splitext(filename)

    # Populate ICD10 objects from either JSON or XML
    if ext == '.json':
        with open(path, 'r') as f:
            json_objects = json.load(f)
        objects = [ICD10.from_json(i) for i in json_objects]
        print "Loaded %s objects from %s" % (len(objects), path)

    else:
        objects = parse_xml_file(path)
        with open("%s.json" % filename, 'w') as f:
            json.dump([i.to_json() for i in objects], f, indent=4)
        print "Dumped %s objects to %s.json" % (len(objects), filename)

    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)

    if not index.exists_in(INDEX_DIR, indexname="icd10"):
        ix = create_in(INDEX_DIR, schema=ICD10_SCHEMA, indexname="icd10")
        print "Created ICD10 index"

    # Store ICD10 objects in index
    if command == 'store':
        ix = open_dir(INDEX_DIR, indexname="icd10")
        writer = ix.writer()
        for obj in objects:
            writer.add_document(**obj.get_whoosh_args())
        writer.commit()
        print "Stored %s ICD10 objects in index" % len(objects)

    # Create or empty ICD10 index
    elif command == 'clean':
        ix = create_in(INDEX_DIR, schema=ICD10_SCHEMA, indexname="icd10")
        print "Emptied ICD10 index"

    # Unknown command
    elif command:
        print "Unknown command '%s'" % command
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
