#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

try:
    import ujson as json
except ImportError:
    import json


def parse_xml_file(path):
    tree = ET.parse(path)
    return tree.getroot()


def traverse_tree(root):
    nodes = root.findall('{http://www.w3.org/2002/07/owl#}Class')
    print "Nodes:", len(nodes)
    for node in nodes:
        print node.attrib


def main(script, path=None):
    if path is None:
        print "Need to supply icd10 file or json file to parse"
        sys.exit(2)

    root = parse_xml_file(path)
    traverse_tree(root)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
