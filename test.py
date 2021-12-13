import sys
import pdfplumber
import re
from functools import cmp_to_key
from commands import *

yTolerance = 5

def extractData(page):
    page = page.crop((0, 180, 595.275, 841.890))
    text = page.extract_text(y_tolerance=yTolerance)
    chars = page.chars
    # words = page.extract_words(extra_attrs=["fontname"])
    return text,chars

def processData(text, chars):
    def cmpTuple(first, second):
        fBot = first['bottom']
        sBot = second['bottom']
        if abs(fBot - sBot) < yTolerance:
            return first['x0'] - second['x0']
        else:
            return fBot - sBot
    chars.sort(key=cmp_to_key(cmpTuple))
    charsInd = 0
    proccessed = ''
    for textChar in text:
        if textChar != chars[charsInd]['text']:
            proccessed += textChar
        else:
            if chars[charsInd]['fontname'][7:] == 'Sepran':
                # txt += 'ჭ'
                proccessed += textChar
            else:
                proccessed += textChar
            charsInd += 1
    return proccessed

def splitData(text):
    found = re.findall("\d\).|❑", text)
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
        for page in pdf.pages:
            text, chars = extractData(page)
            processed += processData(text, chars)
        splited = splitData(processed)
        interaction(splited)  
   
if __name__ == '__main__':
    main()
