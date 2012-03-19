#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module for parsing various data files and to convert them to JSON.

Usage: 'python3 parse.py <folder_or_path>'

Examples:
    Convert icd10no.xml to etc/icd10no.json:
        'python3 parse.py ../data/icd10no.xml'
    Parse nlh html files into etc/therapy.json:
        'python3 parse.py ../data/nlh/'
    Convert patient cases into etc/cases.json:
        'python3 parse.py ../data/cases/'
"""
import os
import sys
import time
import string
import json
from html.parser import HTMLParser
from xml.etree import ElementTree

from data import ATC, ICD, PatientCase, Therapy, get_stopwords


class NLHParser(HTMLParser):
    """Parser for Norwegian Legemiddelhandboka HTML pages."""

    _section_classes = ('seksjon2', 'seksjon3', 'seksjon4', 'seksjon8')
    _ignore_tags = ('br', 'input', 'img', 'tr', 'hr')
    _title_tags = ('h1', 'h2', 'h3', 'h4', 'h5')

    def __init__(self, *args, **vargs):
        super().__init__(*args, **vargs)

        self.actions = []  # Stack for actions to perform
        self.chapters = []  # Stack for chapters

    def _get_attr(self, attrs, key):
        """Get an attribute value from set of 'attrs'."""
        for tmp, value in attrs:
            if key == tmp:
                return value
        return None

    def _split_title(self, title):
        """Split a chapter into code and title."""
        i = 2  # Code can start with *T
        while i < len(title):
            if title[i] not in string.digits and title[i] != '.':
                break
            i += 1
        return title[:i], title[i:]

    def _force_end_chapter(self):
        """Force end of a chapter when a new chapter starts."""
        while self.actions:
            if self.actions[-1][0] == 'end_chapter':
                self.handle_endtag()
                break
            self.handle_endtag()

    def handle_starttag(self, tag, attrs):
        """Handle the start of a HTML tag."""
        if tag in self._ignore_tags:
            return  # Has optional end-tag

        action = 'pop'
        class_ = self._get_attr(attrs, 'class')

        # Start a new chapter
        if ((tag == 'section' and self._get_attr(attrs, 'id') == 'page')
                or (tag == 'div' and class_ in self._section_classes)):
            self.chapters.append(Therapy())
            action = 'end_chapter'

        elif self.chapters:
            if tag in self._title_tags and self.chapters[-1].code is None:
                action = 'store_title'
            elif tag == 'div' and class_ in ('def', 'tone'):
                self.actions[-1][1].append('\n')
                if class_ == 'tone':
                    action = 'discard'
            elif tag == 'div' and class_ in ('revidert', 'forfatter'):
                action = 'discard'
            elif tag == 'a':
                action = 'store_link'
            elif tag == 'h5':
                action = 'add_colon'

        self.actions.append([action, []])

    def handle_data(self, data):
        """Handle text."""
        if self.actions:
            self.actions[-1][1].append(data.strip())

    def handle_endtag(self, tag=''):
        """Handle the end of an HTML tag."""
        if tag in self._ignore_tags or not self.actions:
            return

        # Broken HTML means that chapters might not be ended
        if tag == 'html':
            while self.chapters:
                self._force_end_chapter()
            return

        action, data = self.actions.pop()
        data = ' '.join(i for i in ''.join(data).split(' ') if i)

        obj = self.chapters[-1] if self.chapters else None

        if action == 'add_colon':
            data += ': '
        if action == 'discard':
            pass
        elif action == 'store_title':
            obj.code, obj.title = self._split_title(data)
        elif action == 'store_link':
            obj.links.append(data)
            self.actions[-1][1].append(' %s ' % data)
        elif action == 'end_chapter':
            obj.text += data
            self.chapters.pop()
            if obj.code is not None:  # Broken html, T17.2 & T19.7
                if obj.code[0] == '*':
                    obj.code = obj.code[1:]
                Therapy.ALL[obj.code] = obj
        else:
            if data and self.actions:
                self.actions[-1][1].append(data)

    def handle_charref(self, name):
        """Handle weird html characters."""
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        if self.actions:
            self.actions[-1][1].append(c)


def parse_html_file(path):
    """Parse Norwegian Legemiddelhandboka HTML file 'path'."""
    parser = NLHParser(strict=True)
    with open(path, 'r') as f:
        parser.feed(f.read())
        parser.close()


def preprocess_html_file(in_path, out_path):
    """Preprocess NLH HTML files.

    Change encoding to UTF-8 and remove unnecessary tags etc.
    """
    with open(in_path, 'r', encoding='iso-8859-1') as f1:
        with open(out_path, 'w') as f2:
            # Remove uneceseary carrier returns
            lines = [i.rstrip() for i in f1.readlines()]
            # Remove most of <head> and <footer>
            lines = lines[:3] + lines[4:5] + lines[28:-10] + lines[-4:]
            # Save lines to output file
            f2.write('\n'.join(lines))


def parse_xml_file(path):
    """Parse an XML file which contains ICD10 codes.

    Returns a list of ICD objects which are populated from the file.
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

    # Traverse nodes to create and populate ICD objects
    objects = []
    for node in nodes:
        obj = ICD()
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
            ICD.ALL[obj.short] = obj
        else:
            del obj
    return objects


def parse_pro_file(path):
    """Parse a Prolog fact file which contains ATC codes.

    Returns a list of ATC objects which are populated from the file.
    """
    objects = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('atcname( [') and line.endswith(').\n'):
                code, rest = line[10:-3].split(']', 1)
                code = ''.join(code.split(',')).upper()
                name = rest.split("'")[1]
                objects.append(ATC(code, name))
    return objects


def parse_case_file(path, stopwords=get_stopwords()):
    """Read lines from case file in 'path'."""
    # Read in lines from case files
    with open(path) as f:
        text = []
        for line in f.readlines():
            line = ' '.join(i for i in line.strip().split(' ')
                                    if i.lower() not in stopwords)
            if line:
                if line[-1] == '.':
                    line = line[:-1]  # Remove period from queries
                text.append(line)

    filename, ext = os.path.splitext(os.path.split(path)[1])
    PatientCase(filename.replace('case', ''), '\n'.join(text))


def main(script, folder_or_path=''):
    """Parse various data files and convert them to JSON files.

    Usage: 'python3 parse.py <folder_or_path>'
    """
    if not os.path.exists(folder_or_path):
        print("Error: must be given a valid path '%s'" % folder_or_path)
        print("Usage: python3 parse.py <path>")
        sys.exit(2)

    # Accept path to either a folder or a file
    paths = []
    if not os.path.isdir(folder_or_path):
        paths.append(folder_or_path)
    else:
        for path in os.listdir(folder_or_path):
            full_path = os.path.normpath(os.path.join(folder_or_path, path))
            if not os.path.isdir(full_path):
                paths.append(full_path)
        paths.sort()

    # Parse or preprocess files
    now = time.time()
    classes = set()
    for path in paths:
        file_ext = os.path.splitext(path)[1]
        if file_ext == '.pro':
            parse_pro_file(path)
            classes.add(ATC)
        elif file_ext == '.xml':
            parse_xml_file(path)
            classes.add(ICD)
        elif file_ext == '.htm':
            #preprocess_html_file(path, path + 'l')
            pass
        elif file_ext == '.html':
            parse_html_file(path)
            classes.add(Therapy)
        elif file_ext == '.txt':
            parse_case_file(path)
            classes.add(PatientCase)
    print("Parsed %s in %.5f seconds" % (folder_or_path, time.time() - now))

    # Dump to JSON
    for cls in classes:
        now = time.time()
        try:
            objects = cls.ALL.values()
        except AttributeError:
            objects = cls.ALL
        with open(cls._JSON, 'w') as f:
            json.dump([i.to_json() for i in objects], f, indent=4)
        print("Dumped %s objects to %s in %.2f seconds" % (
                len(objects), cls._JSON, time.time() - now))

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
