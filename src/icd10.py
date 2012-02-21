#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

try:
    import ujson as json
except ImportError:
    import json


class ICD10(object):

    def __init__(self):
        self.inclusion = []
        self.exclusion = []
        self.terms = []
        self.synonym = []

        self.short = None
        self.code = None
        self.label = None
        self.formatted = None
        self.type = None
        self.icpc2_label = None

    def __str__(self):
        output = "%s: %s" % (self.short, self.label)
        return output.encode('ascii', 'ignore')


def parse_xml_file(path):
    tree = ET.parse(path)
    return tree.getroot()


def simplify_tag(tag):
    return tag.split('}')[1]


def traverse_tree(root):
    objects = []
    nodes = root.findall('{http://www.w3.org/2002/07/owl#}Class')

    for node in nodes:
        obj = ICD10()
        for child in node:
            tag = simplify_tag(child.tag)

            if tag == 'label':
                obj.label = child.text
            elif tag == 'code_compacted':
                obj.short = child.text
            elif tag == 'code_formatted':
                obj.formatted = child.text
            elif tag == 'subClassOf':
                pass
            elif tag == 'umls_atomId':
                pass
            elif tag == 'umls_conceptId':
                pass
            elif tag == 'umls_tui':
                pass
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
                    obj.synonym.append(child.text.strip())
            elif tag == 'inclusion':
                obj.inclusion.append(child.text)
            elif tag == 'exclusion':
                obj.exclusion.append(child.text)
            else:
                print simplify_tag(child.tag), ":", child.text, child.tail

        objects.append(obj)
    return objects


def main(script, path=None):
    if path is None:
        print "Need to supply icd10 file or json file to parse"
        sys.exit(2)

    # Parse XML file
    root = parse_xml_file(path)
    objects = traverse_tree(root)

    # Generate a json file
    folder, filename = os.path.split(path)
    filename, ext = os.path.splitext(filename)
    with open("%s.json" % filename, 'w') as f:
        json.dump(objects, f)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
