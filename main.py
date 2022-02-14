from string import punctuation
import sys
import pdfplumber
import json
from functools import cmp_to_key
from commands import *
from utils import *
import requests
import dataclasses
import numpy as np

sepranUrmiDict = {}
simonSpecialChar = 'ܔ'
simonSpecial = {'text' : simonSpecialChar, 'fontname': 'HCFQDX+Sepran'}
pageWidth = 595.275
pageHeight = 841.890
pageCropTop = 170
pageMiddle = 291.4
pageLeftX = 92.771
pageRightX = 490.538
apiUrl = 'http://192.168.131.160:3030/unit-content'
splitTextRegex = '\d\).|❑|<title>'
unit = ''

def readJson(file):
    global sepranUrmiDict
    with open(file) as json_file:
        sepranUrmiDict = json.load(json_file)

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
        if ind and sameY(ch, chars[ind - 1]) and abs(ch['x0'] - chars[ind - 1]['x0']) > 20 and ch['text'] != ' ':
            newChars.append({'text': commonDelimiter, 
            'fontname' : 'HCFQDX+Century'})
        elif ind and not sameY(ch, chars[ind - 1]):
            newChars.append({'text':'\n'})
        newChars.append(ch)

    # print(''.join([char['text'] for char in newChars]))
    return newChars

def convertToAramaic(line):
    seprInd = -1
    inserts = []
    prevWord = ''
    for i in range(len(line)):
        # if line[i]['text'] == '"':
        #     print(line[i]['fontname'])
        if line[i]['text'] in '.?:,[]+-"' and prevWord and line[i]['fontname'][7:]:
            tempInd = i + 1
            seps = 0
            totChars = 2
            while tempInd < len(line) and totChars:
                if line[tempInd]['text'] == ' ' or not line[tempInd]['text'] or line[tempInd]['text'] in punctuation: 
                    tempInd += 1
                    continue
                if line[tempInd]['fontname'][7:] == 'Sepran': seps += 1
                totChars -= 1
                tempInd += 1

            if prevWord[7:] == 'Sepran' and seps > 0:
                line[i]['fontname'] = 'HCFQDX+Sepran'
                if line[i]['text'] == ',':
                    line[i]['text'] = '#'
                elif line[i]['text'] == '+':
                    line[i]['text'] = '\u0e2e'
                elif line[i]['text'] == '-':
                    line[i]['text'] = '\u0e2d'

            else:
                line[i]['fontname'] = 'HCFQDX+Century'

            prevWord = ''

        if line[i]['fontname'][7:] == 'Sepran':
            # if not line[i]['text'] in sepranUrmiDict: print(line[i]['text'])
            if not(i and line[i - 1]['fontname'][7:] != 'Sepran' and line[i]['text'] in '()'):
                line[i]['text'] = sepranUrmiDict[line[i]['text']] if line[i]['text'] in sepranUrmiDict else 'ყ' + line[i]['text'] + 'ყ'
            seprInd = i if seprInd == -1 else seprInd
        else:
            # if line[i]['text'] in '-+': #-+.
            #     # line[i]['text'] = '⠀-⠀'
            #     line[i]['text'] = '‎' + line[i]['text']
                
            if i and line[i - 1]['fontname'][7:] == 'Sepran':
                index = i
                if line[i - 1]['text'] == ' ': index -= 1
                if line[seprInd]['text'] == ' ': seprInd += 1

                if isAramLetter(''.join([ch['text'] for ch in line[seprInd: index]])):
                    inserts.append(index)
                    
                line[seprInd: index] = line[seprInd: index][::-1]
                seprInd = -1
        
        if line[i]['text'] != ' ' and not line[i]['text'] in punctuation:
            prevWord = line[i]['fontname']

    if seprInd != -1: 
        if isAramLetter(''.join([ch['text'] for ch in line[seprInd:]])):
            line.insert(seprInd, simonSpecial)
        line[seprInd:] = line[seprInd:][::-1]
    
    for i in range(len(inserts)):
        line.insert(inserts[i]+i, simonSpecial)

    return line

def processLine(line):
    leftX = float(line[0]['x0'])
    rightX = float(line[-1]['x1'])
    if abs((leftX + rightX) / 2 - pageMiddle) < 5 and leftX > pageLeftX + 12:
        line.insert(0, {'text': '<title>', 'fontname': 'HCFQDX+Century'})

    line = changeFont(line, '?', '^', 'HCFQDX+Sepran')
    # line = changeFont(line, ',', '#', 'HCFQDX+Sepran')
    line = changeFont(line, ' ', ' ', 'HCFQDX+Sepran')
    # line = changeFont(line, '+', '\u0e2e', 'HCFQDX+Sepran')
    # line = changeFont(line, '-', '\u0e2d', 'HCFQDX+Sepran')
    # line = changeFont(line, ".", '@', 'HCFQDX+Sepran')
    # line = changeFont(line, '.', '@', 'HCFQDX+Sepran')
    aramaic = convertToAramaic(line)

    return aramaic

def processData(chars):
    splited = splitCharsBy(chars, '\n')
    proccessedLines = [processLine(line) for line in splited]
    
    joined = joinCharsBy(proccessedLines, '\n')
    return ''.join([mp['text'] for mp in joined])

def splitIfTag(tasks, index):
    text = tasks[index]
    splited = splitTextByRegex(text, '<header>|<simple>|<grid>|<title>')
    # Even if tag doesn't exist returns same txt
    tasks[index] = splited[0]
    for ind, txt in enumerate(splited[1:]):
        tasks.insert(index + ind + 1, txt)

def sendDecision(data):
    print('Send this data?')
    print(data)
    return int(input('Enter 0, 1, 2: '))

def mergeTitles(textArr):
    temp = copy.deepcopy(textArr)
    for ind, task in enumerate(textArr[1:]):
        if '<title>' in task and '<title>' in textArr[ind]:
            temp[ind + 1] = textArr[ind] + task
  
    temp.append('')
    result = []
    for ind, task in enumerate(temp[:-1]):
        if '<title>' in task and '<title>' in temp[ind + 1]:
            continue
        result.append(task)
    return result

def handleCommand(task, command, splited, tasks, index):
    try:
        task = re.sub('❑|<title>|<header>|<simple>|<grid>', '', task)
        task = delNewLineBegin(task)
        returned, data = commands[command](task, *(splited[1:]))
        if returned == CommandReturn.nano:
            with open('temp.txt', 'r') as f:
                tasks[index] = f.read()
                splitIfTag(tasks, index)
        elif returned not in [CommandReturn.help, CommandReturn.header, CommandReturn.grid, 
                                CommandReturn.exerciseTitle, CommandReturn.empty, CommandReturn.prev]:
            query = Request(inUnitIndex=index, ascUnitName=unit, type=returned.name, data={})
            # if returned not in [CommandReturn.TITLE, CommandReturn.BULLET, CommandReturn.TABLE]:
            decision = sendDecision(data)
            if not decision : return index
            elif decision == 2 : data = {}
            if not isinstance(data, dict) : data = dataclasses.asdict(data)
            query.data = data
            print(requests.post(apiUrl, json=dataclasses.asdict(query)).text)
        elif returned not in [CommandReturn.empty, CommandReturn.prev]:
            decision = sendDecision(data)
            if not decision : return index
            elif decision == 1 : return index + 1
        
        if returned in [CommandReturn.empty, CommandReturn.grid, CommandReturn.header, 
                        CommandReturn.exerciseTitle, CommandReturn.bullet, CommandReturn.title] : index += 1
        if returned in [CommandReturn.prev]: index -= 1
    except Exception as _:
        print('---  Wrong command!!!  ---')
    
    return index

def interaction(tasks, index = 0):
    try:
        while index < len(tasks):
            task = tasks[index]
            print('\nNext Task:')
            print(task)
            comm = input('Enter a command ("help" for help): ')
            splited = comm.split(' ')
            command = splited[0]
            index = handleCommand(task, command, splited, tasks, index)
    except KeyboardInterrupt as _:
        save = input("\nSave state? ")
        if save != '0':
            with open("{}.json".format(unit), "w") as f:
                # jsonstr = json.dumps(tasks)
                stateData = {
                    'index': index,
                    'data':tasks
                }
                json.dump(stateData, f)
        exit(0)

def main():
    global unit
    unitFile = sys.argv[1]
    unit = unitFile[:-4]
    readJson('sepran-urmi.json')
    load = input('Load previous state? ')
    if load == '0':
        with pdfplumber.open(unitFile) as pdf:
            processed = ''
            for page in pdf.pages:
                _, chars = extractData(page)
                newChars = processChars(chars)
                processed += processData(newChars)
            # print(processed)
            splited = splitTextByRegex(processed, splitTextRegex)
            merged = mergeTitles(splited)
            merged.append('The End 🔥')
            interaction(merged) 
    else:
        ind = 0
        try:
            splited = load.split(' ')
            ind = int(splited[1])
        except:
            pass
        with open("{}.json".format(unit), "r") as f:
                # jsonstr = json.dumps(tasks)
                stateData = json.load(f)
                prevInd = stateData['index']
                arr = stateData['data']
                finalInd = prevInd if ind == -1 else ind
                interaction(arr, finalInd)
                # json.dump(tasks, f)
   
if __name__ == '__main__':
    main()
