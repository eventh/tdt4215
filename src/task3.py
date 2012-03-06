import sys
import time
from operator import itemgetter
from pprint import pprint

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.index import open_dir, create_in

import tasks
from nlh import populate_chapters
from codes import create_index, INDEX_DIR


class Task3:

    SCHEMA = Schema(code=ID(stored=True),
                title=ID(stored=True), type=ID(stored=True), text=TEXT)

    NAME = 'task3'

    ALL = {}

    _fields = ('code', 'text', 'title', 'type')

    def __init__(self, code, text, title=None, type=None):
        Task3.ALL[code] = self
        self.code = code
        self.text = text
        self.title = title
        self.type = type

    def to_index(self):
        return {i: getattr(self, i) for i in self._fields if getattr(self, i)}


def checkSimilarities(cases, chapters):
    print('Case # | Relevant chapter | Hits')

    for name, lines in sorted(cases.items(), key=itemgetter(0)):
        case = '\n'.join(lines)
        words_case = case.split()


        chapter_highest = ''
        highest_sum = 0
        for chapter in chapters:
            sum_ = 0
            words = chapter.text.split()
            for word in words_case:
                if word in words:
                    sum_ += 1
            sum_ = sum_ / len(words) if words else sum_
            if sum_ > highest_sum:
                highest_sum = sum_
                chapter_highest = chapter

        print("%s | %s - %s | %f" % (name,
                chapter_highest.code, chapter_highest.title, highest_sum))


def main(script, command=''):
    cases = tasks.read_cases_from_files('etc/')
    chapters = populate_chapters()

    for name, lines in cases.items():
        Task3(name, '\n'.join(lines), type='case')
    for chapter in chapters:
        Task3(chapter.code, chapter.text, chapter.title, type='chapter')

    if command == 'search':
        create_index(Task3)
        ix = open_dir(INDEX_DIR, indexname=Task3.NAME)
        reader = ix.reader()
        pprint(reader.most_distinctive_terms('text'))
        #qp = QueryParser('text', schema=ix.schema, group=OrGroup)


    elif command == 'store':
        create_index(Task3)
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=Task3.NAME)
        with ix.writer() as writer:
            for obj in Task3.ALL.values():
                writer.add_document(**obj.to_index())
        print("Stored %s %s objects in index in %.2f seconds" % (
                len(Task3.ALL), Task3.__name__, time.time() - now))


    elif command in ('clean', 'clear'):
        create_index(Task3)
        ix = create_in(INDEX_DIR, schema=Task3.SCHEMA, indexname=Task3.NAME)
        print("Emptied %s index" % Task3.__name__)

    else:
        checkSimilarities(cases, chapters)


if __name__ == '__main__':
    main(*sys.argv)
