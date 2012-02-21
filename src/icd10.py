#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for converting icd10no.xml file to json format.
"""
import sys
import os
import json

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


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

    @classmethod
    def from_json(cls, values):
        obj = cls()
        for i in cls.lists + cls.fields:
            setattr(obj, i, values[i])
        return obj


def parse_xml_file(path):
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

        objects.append(obj)
    return objects


def main(script, path=None, load=False):
    if path is None:
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

    else:
        # Build ICD10 objects from XML file
        objects = parse_xml_file(path)

        # Generate a json file
        with open("%s.json" % filename, 'w') as f:
            json.dump([i.to_json() for i in objects], f, indent=4)

    # Load ICD10 objects into whoosh database
    if load:
        pass

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
