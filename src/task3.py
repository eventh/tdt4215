import json
import tasks
import nlh

global result_chapter
global result_hits

def checkSimilarities():
    result_chapter = []
    result_hits = []
    for i in range(1, 9):
        cases = tasks.read_cases_from_files('etc/case'+str(i)+'.txt')
        case = '\n'.join(list(cases.values())[0])
        words_case = case.split()
        chapters = nlh.populate_chapters()
        chapter_highest = ''
        highest_sum = 0 
        for chapter in chapters:
            sum = 0
            words = chapter.text.split()
            for word in words_case:
                if word in words:
                    sum += 1
            if sum > highest_sum:
                highest_sum = sum
                chapter_highest = chapter
        result_chapter.append(chapter_highest)
        result_hits.append(highest_sum)
    labels = ['Case #', 'Relevant chapter', 'Hits']
    for j in range(1, 9):
        values = [j, result_chapter[j-1], result_hits[j-1]]
        paddedLabels = []
        paddedValues = []
        dividers = []
        dblDividers = []

        for label, value in zip(labels, values):
            value = str(value)
            columnWidth = max(len(label), len(value))
            paddedLabels.append(label.center(columnWidth))
            paddedValues.append(value.center(columnWidth))
            dividers.append('-' * columnWidth)
            dblDividers.append('=' * columnWidth)

        print('+-' + '-+-'.join(dividers) + '-+')
        print('| ' + ' | '.join(paddedLabels) + ' |')
        print('+=' + '=+='.join(dblDividers) + '=+')
        print('| ' + ' | '.join(paddedValues) + ' |')
        print('+-' + '-+-'.join(dividers) + '-+')



checkSimilarities()
        

