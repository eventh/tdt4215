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
    print root


def main(script, path=None):
    if path is None:
        print "Need to supply icd10 file or json file to parse"
        sys.exit(2)

    root = parse_xml_file(path)
    traverse_tree(root)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
