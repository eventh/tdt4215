import sys
import time
import math
from operator import itemgetter
from pprint import pprint

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.index import open_dir, create_in
from whoosh.analysis import StandardAnalyzer

from nlh import populate_chapters
from codes import create_index, INDEX_DIR
from tasks import read_stopwords, read_cases_from_files


class Task3:

    SCHEMA = Schema(code=ID(stored=True, unique=True),
                title=ID(stored=True), type=ID(stored=True),
                text=TEXT(vector=True,
                    analyzer=StandardAnalyzer(stoplist=read_stopwords())))

    NAME = 'task3'

    ALL = {}

    _fields = ('code', 'text', 'title', 'type')

    def __init__(self, code, text, title=None, type=None):
        Task3.ALL[code] = self
        self.code = code
        self.text = text
        self.title = title
        self.type = type
        self.vector = None

    def to_index(self):
        return {i: getattr(self, i) for i in self._fields if getattr(self, i)}

    def set_vector(self, searcher, doc_num):
        self.vector = {}
        for term, score in searcher.key_terms([doc_num], 'text', numterms=1000):
            self.vector[term] = score * searcher.idf('text', term)

    @classmethod
    def create_vectors(cls):
        ix = open_dir(INDEX_DIR, indexname=cls.NAME)
        reader = ix.reader()
        with ix.searcher() as searcher:
            for doc_num in searcher.document_numbers():
                if reader.has_vector(doc_num, 'text'):
                    code = searcher.stored_fields(doc_num)['code']
                    cls.ALL[code].set_vector(searcher, doc_num)
                else:
                    print(searcher.stored_fields(doc_num))

    @classmethod
    def populate(cls, cases, chapters):
        for name, lines in cases.items():
            cls(name, '\n'.join(lines), type='case')
        for chapter in chapters:
            if chapter.text:
                cls(chapter.code, chapter.text, chapter.title, type='chapter')


def check_similarities(cases, chapters):
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
    cases = read_cases_from_files('etc/')
    chapters = populate_chapters()
    Task3.populate(cases, chapters)

    if command == 'search':
        create_index(Task3)
        now = time.time()
        Task3.create_vectors()
        print("Created vectors in %.2f seconds" % (time.time() - now))

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
        check_similarities(cases, chapters)
        print(calculate_vectordistance())


if __name__ == '__main__':
    main(*sys.argv)
