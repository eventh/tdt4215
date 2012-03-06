import sys
from operator import itemgetter

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED

import tasks
from nlh import populate_chapters
from codes import create_index


class Task3:

    SCHEMA = Schema(code=ID(stored=True),
                title=ID(stored=True), type=ID(stored=True), text=TEXT)

    NAME = 'task3'

    _fields = ('code', 'text', 'title', 'type')

    def __init__(self, code, text, title=None, type=None):
        self.code = code
        self.text = text
        self.title = title
        self.type = type

    def to_index(self):
        return {i: getattr(self, i) for i in self._fields
                    if getattr(self, i) is not None}


def checkSimilarities():
    cases = tasks.read_cases_from_files('etc/')
    print('Case # | Relevant chapter | Hits')

    for name, lines in sorted(cases.items(), key=itemgetter(0)):
        case = '\n'.join(lines)
        words_case = case.split()

        chapters = populate_chapters()

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
    if command == 'store':
        chapters = populate_chapters()

        pass
    else:
        checkSimilarities()


if __name__ == '__main__':
    main(*sys.argv)
