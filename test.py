import sys
import pdfplumber
import re
from functools import cmp_to_key
from commands import *

leftx = 138.3
rightx = 542.7

yTolerance = 5

def charY(char):
    return (char['bottom'] + char['top']) / 2

def sameY(char1, char2):
    return abs(charY(char1) - charY(char2)) <= yTolerance

def extractData(page):
    page = page.crop((0, 170, 595.275, 841.890))
    text = page.extract_text(y_tolerance=yTolerance)
    chars = page.chars
    # words = page.extract_words(extra_attrs=["fontname"])
    return text,chars

def processData(text, chars):
    def cmpTuple(first, second):
        firstY = charY(first)
        secondY = charY(second)
        if sameY(first, second):
            return first['x0'] - second['x0']
        else:
            return firstY - secondY
    chars.sort(key=cmp_to_key(cmpTuple))

    newChars = []
    for ind, ch in enumerate(chars):
        if ind and sameY(ch, chars[ind - 1]) and abs(ch['x0'] - chars[ind - 1]['x0']) > 15 and ch['text'] != ' ':
            newChars.append({'text': ' ', 
            'fontname' : chars[ind - 1]['fontname']})
        elif ind and not sameY(ch, chars[ind - 1]):
            newChars.append({'text':'\n'})
        newChars.append(ch)


    charsInd = 0
    proccessed = ''

    for textChar in text:
        if textChar != chars[charsInd]['text']:
            proccessed += textChar
        else:
            # if charsInd and chars[charsInd]['x0'] > 150 and abs(charY(chars[charsInd - 1]) - charY(chars[charsInd])) > 10:
            #     proccessed += '<title>'
            #     proccessed += textChar
            if chars[charsInd]['fontname'][7:] == 'Sepran':
                # txt += 'ჭ'
                proccessed += textChar
            else:
                proccessed += textChar
            charsInd += 1
    charebi = ''
    for i in newChars:
        charebi += i['text']
    print(charsInd, len(chars))
    print(charebi == text)
    print(charebi)
    print(text)
    return proccessed

def splitData(text):
    found = re.findall("\d\).|❑|<title>", text)
    # Split text by found indices of splitting strs
    fromInd = -1
    indices = []
    for reg in found:
        # find index of current reg from previous found reg index 
        fromInd = text.index(reg, fromInd + 1)
        indices.append(fromInd)
    # Append all tasks by their indices 
    result = [text[indices[ind - 1] : regInd] if ind else text[:regInd] for ind, regInd in enumerate(indices)]
    result.append(text[indices[-1]:])
    return result

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
            returned = commands[command](task, *splited[1:])
            if returned == CommandReturn.NANO:
                with open('temp.txt', 'r') as f:
                    tasks[index] = f.read()
            elif returned == CommandReturn.NEXT:
                index += 1
        except:
            print('Wrong command!')

def main():
    with pdfplumber.open(sys.argv[1]) as pdf:
        processed = ''
        for page in pdf.pages[0:1]:
            text, chars = extractData(page)
            processed += processData(text, chars)
        splited = splitData(processed)
        interaction(splited)  
   
if __name__ == '__main__':
    main()
