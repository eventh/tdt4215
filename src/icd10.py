#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for converting icd10no.xml file to json format.
"""
import sys
import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

#try:
#    import ujson as json
#except ImportError:
import json


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
        values = {}
        for i in self.lists:
            values[i] = getattr(self, i)
        for i in self.fields:
            values[i] = getattr(self, i)
        return values


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


def main(script, path=None):
    if path is None:
        print "Need to supply icd10 file or json file to parse"
        sys.exit(2)

    # Build ICD10 objects from XML file
    objects = parse_xml_file(path)

    # Generate a json file
    folder, filename = os.path.split(path)
    filename, ext = os.path.splitext(filename)
    with open("%s.json" % filename, 'w') as f:
        json.dump([i.to_json() for i in objects], f, indent=4)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
