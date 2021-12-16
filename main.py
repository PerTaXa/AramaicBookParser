import sys
import pdfplumber
from functools import cmp_to_key
from commands import *
from utils import *

pageWidth = 595.275
pageHeight = 841.890
pageCropTop = 170
pageMiddle = 291.4
pageLeftX = 92.771
pageRightX = 490.538

def extractData(page):
    page = page.crop((0, pageCropTop, pageWidth, pageHeight))
    text = page.extract_text(y_tolerance=yTolerance)
    chars = page.chars
    # words = page.extract_words(extra_attrs=["fontname"])
    return text,chars

def processChars(chars):
    chars.sort(key=cmp_to_key(pageSortCmp))

    newChars = []
    for ind, ch in enumerate(chars):
        if ind and sameY(ch, chars[ind - 1]) and abs(ch['x0'] - chars[ind - 1]['x0']) > 15 and ch['text'] != ' ':
            newChars.append({'text': commonDelimiter, 
            'fontname' : chars[ind - 1]['fontname']})
        elif ind and not sameY(ch, chars[ind - 1]):
            newChars.append({'text':'\n'})
        newChars.append(ch)

    return newChars

def processData(chars):
    splited = splitCharsBy(chars, '\n')
    for line in splited:
        leftX = float(line[0]['x0'])
        rightX = float(line[-1]['x1'])
        if abs((leftX + rightX) / 2 - pageMiddle) < 1 and leftX > pageLeftX + 10:
            line.insert(0, {'text': '<title>'})
    joined = joinCharsBy(splited, '\n')
    result = ''
    for mp in joined:
        result += mp['text']
    return result

def splitIfTag(tasks, index):
    text = tasks[index]
    splited = splitTextByRegex(text, '<table>|<simple>|<grid>')
    # Even if tag doesn't exist returns same txt
    tasks[index] = splited[0]
    for ind, txt in enumerate(splited[1:]):
        tasks.insert(index + ind + 1, txt)

def interaction(tasks):
    index = 0
    while index < len(tasks):
        task = tasks[index]
        print('\nNext Task:')
        print(task)
        comm = input('Enter a command ("help" for help): ')
        splited = comm.split(' ')
        command = splited[0]
        try:
            returned = commands[command](task, *(splited[1:]))
            if returned == CommandReturn.NANO:
                with open('temp.txt', 'r') as f:
                    tasks[index] = f.read()
                    splitIfTag(tasks, index)
            elif returned == CommandReturn.NEXT:
                index += 1
        except Exception as err:
            print(err)
            print('Wrong command!')

def main():
    with pdfplumber.open(sys.argv[1]) as pdf:
        processed = ''
        for page in pdf.pages:
            _, chars = extractData(page)
            newChars = processChars(chars)
            processed += processData(newChars)
        splited = splitTextByRegex(processed, '\d\).|❑|<title>')
        splited = splited[13:]
        interaction(splited)  
   
if __name__ == '__main__':
    main()
