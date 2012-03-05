import json
import tasks
import nlh

def checkSimilarities():
    for i in range(1, 8):
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
        print(chapter_highest, highest_sum)

checkSimilarities()
        

