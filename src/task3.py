import sys
from operator import itemgetter

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED

import tasks
from nlh import populate_chapters
from codes import create_index
import math


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

def calculate_vectordistance():
    vector_1 = [0.5, 0, 0]
    vector_2 = [1, 0.5, 1]
    AB_dotproduct = 0
    A_magnitude = 0
    B_magnitude = 0
    for i in range(len(vector_1)):
        AB_dotproduct += (vector_1[i] * vector_2[i])
        A_magnitude += vector_1[i]**2
        B_magnitude += vector_2[i]**2
        
    AB_magnitude = math.sqrt(A_magnitude)*math.sqrt(B_magnitude)
    return AB_dotproduct / AB_magnitude

    
    

def main(script, command=''):
    print(calculate_vectordistance())
    if command == 'store':
        chapters = populate_chapters()

        pass
    else:
        checkSimilarities()


if __name__ == '__main__':
    main(*sys.argv)
