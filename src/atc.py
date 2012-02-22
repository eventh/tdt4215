#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A module for loading ATC objects.

Anatomical Therapeutic Chemical classification system of drugs.

The drugs are divided into fourteen main groups (1st level), with
pharmacological/therapeutic subgroups (2nd level). The 3rd and 4th levels
are chemical/pharmacological/therapeutic subgroups and the 5th level is
the chemical substance.
"""
import sys
import os
import json
import time

from whoosh.index import create_in, open_dir, exists_in

from schemas import ATC_SCHEMA, INDEX_DIR


class ATC(object):
    """Anatomical Therapeutic Chemical classification system of drugs."""

    def __init__(self, code, name):
        """Create a new ATC object."""
        self.code = code
        self.name = name

    def __str__(self):
        """Present the object as a string."""
        output = '%s: %s' % (self.code, self.name)
        return output.encode('ascii', 'ignore')

    def to_json(self):
        """Create a dictionary representing the object."""
        return {'code': self.code, 'name': self.name}

    @classmethod
    def from_json(cls, values):
        """Create an object from json value dictionary."""
        return cls(values['code'], values['name'])


def parse_pl_file(path):
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
    """Read ATC objects from file and load into index.

    'path' to the ATC input file, either JSON or .PL format.
    'command' is either 'store' into database or 'clean' database.
    Usage: python atc.py <input file> <store|clean>
    To store ATC in whoosh index from atcname.json file perform:
        'python atc.py atcname.json store'
    """
    if not path:
        print "Need to supply atc file or json file to parse"
        sys.exit(2)

    # Split path in folder, filename, file extension
    folder, filename = os.path.split(path)
    filename, ext = os.path.splitext(filename)

    # Populate ATC objects from either JSON or XML
    if ext == '.json':
        now = time.time()
        with open(path, 'r') as f:
            json_objects = json.load(f)
        objects = [ATC.from_json(i) for i in json_objects]
        print "Loaded %s objects from %s in %.2f seconds" % (
                len(objects), path, time.time() - now)

    else:
        now = time.time()
        objects = parse_pl_file(path)
        with open("%s.json" % filename, 'w') as f:
            json.dump([i.to_json() for i in objects], f, indent=4)
        print "Dumped %s objects to %s.json in %.2f seconds" % (
                len(objects), filename, time.time() - now)

    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)

    if not exists_in(INDEX_DIR, indexname='atc'):
        ix = create_in(INDEX_DIR, schema=ATC_SCHEMA, indexname='atc')
        print "Created ATC index"

    # Store ATC objects in index
    if command == 'store':
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname='atc')
        writer = ix.writer()
        for obj in objects:
            writer.add_document(**obj.to_json())
        writer.commit()
        print "Stored %s ATC objects in index in %.2f seconds" % (
                len(objects), time.time() - now)

    # Empty ATC index
    elif command == 'clean':
        ix = create_in(INDEX_DIR, schema=ATC_SCHEMA, indexname='atc')
        print "Emptied ATC index"

    # Unknown command
    elif command:
        print "Unknown command '%s'" % command
        sys.exit(2)

    sys.exit(None)


if __name__ == '__main__':
    main(*sys.argv)
