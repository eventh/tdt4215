import sys
from operator import itemgetter

import tasks
import nlh


def checkSimilarities():
    cases = tasks.read_cases_from_files('etc/')
    print('Case # | Relevant chapter | Hits')

    for name, lines in sorted(cases.items(), key=itemgetter(0)):
        case = '\n'.join(lines)
        words_case = case.split()

        chapters = nlh.populate_chapters()

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


def main(script):
    checkSimilarities()


if __name__ == '__main__':
    main(*sys.argv)
