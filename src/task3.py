import sys
import time
from math import sqrt, log
from operator import itemgetter

from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.index import open_dir, create_in
from whoosh.formats import Frequency

from nlh import populate_chapters
from codes import create_index, INDEX_DIR
from tasks import read_cases_from_files, ANALYZER


# Inverse Document and Term Frequency Weight functions
def _idf(N, n):
    return log(N / n)  # Inverse frequency
def _idf_smooth(N, n):
    return log(1 + (N / n))  # Inverse frequency smooth
def _idf_prob(N, n):
    return log((N - n) / n)  # Probabilistic inverse frequency
def _tf_log_norm(frequency):
    return 1 + log(frequency)  # Log normalization


class Task3:

    SCHEMA = Schema(code=ID(stored=True, unique=True),
                    text=TEXT(vector=Frequency(), analyzer=ANALYZER))
    NAME = 'task3'
    ALL = {}

    def __init__(self, code, text):
        Task3.ALL[code] = self
        self.code = code
        self.text = text
        self.vector = None

    def __str__(self):
        return self.code

    def to_index(self):
        return {'code': self.code, 'text': self.text}

    def to_json(self):
        return {'code': self.code, 'text': self.text, 'vector': self.vector}

    @classmethod
    def create_vectors(cls):
        now = time.time()
        ix = open_dir(INDEX_DIR, indexname=cls.NAME)
        with ix.searcher() as searcher:
            def idf(term):
                N = searcher.doc_count()
                n = searcher.doc_frequency('text', term)
                return _idf(N, n)

            for doc_num in searcher.document_numbers():
                obj = cls.ALL[searcher.stored_fields(doc_num)['code']]
                obj.vector = {t: _tf_log_norm(w) * idf(t) for t, w in
                              searcher.vector_as('weight', doc_num, 'text')}

        print("Created vectors in %.2f seconds" % (time.time() - now))

    @classmethod
    def populate(cls, cases, chapters):
        for name, lines in cases.items():
            PatientCase(name, '\n'.join(lines))
        for chapter in chapters:
            if chapter.text:
                Therapy(chapter)


class Therapy(Task3):

    ALL = {}

    def __init__(self, chapter):
        Therapy.ALL[chapter.code] = self
        self.title = chapter.title
        self.chapter = chapter
        super().__init__(chapter.code, chapter.text)

    def __str__(self):
        return '%s: %s' % (self.code, self.title)


class PatientCase(Task3):

    ALL = {}

    def __init__(self, code, *args, **vargs):
        PatientCase.ALL[code] = self
        super().__init__(code, *args, **vargs)


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


def calculate_vectordistance(vectors):
    AB_dotproduct = 0
    A_magnitude = 0
    B_magnitude = 0
    for i in range(len(vectors)):
        AB_dotproduct += vectors[i][0] * vectors[i][1]
        A_magnitude += vectors[i][0] ** 2
        B_magnitude += vectors[i][1] ** 2

    AB_magnitude = sqrt(A_magnitude) * sqrt(B_magnitude)
    return AB_dotproduct / AB_magnitude


def match_cases_to_chapters():
    """Match patient cases to therapy chapters."""
    now = time.time()
    therapy = list(Therapy.ALL.values())
    for code, case in sorted(PatientCase.ALL.items(), key=itemgetter(0)):

        results = []
        for chapter in therapy:

            vectors = []
            for term, value in case.vector.items():
                if term in chapter.vector:
                    vectors.append((value, chapter.vector[term]))

            if vectors:
                results.append((chapter, calculate_vectordistance(vectors)))
                print(vectors, calculate_vectordistance(vectors))
                break

        results.sort(key=itemgetter(1), reverse=True)

        # Print results
        print("Case %s" % code)
        for chapter, value in results[:10]:
            print(str(chapter), value)

    print("Matched cases with chapters in %.2f seconds" % (time.time() - now))


def main(script, command=''):
    cases = read_cases_from_files('etc/')
    chapters = populate_chapters()
    Task3.populate(cases, chapters)

    if command == 'search':
        create_index(Task3)
        Task3.create_vectors()
        match_cases_to_chapters()

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
