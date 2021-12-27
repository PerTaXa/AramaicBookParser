import sys
import pdfplumber
import json
from functools import cmp_to_key
from commands import *
from utils import *
import requests
import dataclasses

sepranUrmiDict = {}
simonSpecialChar = 'ܔ'
simonSpecial = {'text' : simonSpecialChar, 'fontname': 'HCFQDX+Sepran'}
pageWidth = 595.275
pageHeight = 841.890
pageCropTop = 170
pageMiddle = 291.4
pageLeftX = 92.771
pageRightX = 490.538
apiUrl = 'http://192.168.30.160:3030/unitContent'
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
        if ind and sameY(ch, chars[ind - 1]) and abs(ch['x0'] - chars[ind - 1]['x0']) > 15 and ch['text'] != ' ':
            newChars.append({'text': commonDelimiter, 
            'fontname' : 'HCFQDX+Century'})
        elif ind and not sameY(ch, chars[ind - 1]):
            newChars.append({'text':'\n'})
        newChars.append(ch)

    return newChars

def convertToAramaic(line):
    seprInd = -1
    inserts = []
    for i in range(len(line)):
        if line[i]['fontname'][7:] == 'Sepran':
            line[i]['text'] = sepranUrmiDict[line[i]['text']] if line[i]['text'] in sepranUrmiDict else 'ყ'
            seprInd = i if seprInd == -1 else seprInd
        else:
            if i and line[i - 1]['fontname'][7:] == 'Sepran':
                if isAramLetter(''.join([ch['text'] for ch in line[seprInd: i]])):
                    inserts.append(i)
                    
                line[seprInd: i] = line[seprInd: i][::-1]
                seprInd = -1
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
    if abs((leftX + rightX) / 2 - pageMiddle) < 5 and leftX > pageLeftX + 10:
        line.insert(0, {'text': '<title>', 'fontname': 'HCFQDX+Century'})
    return convertToAramaic(line)

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
                                CommandReturn.exerciseTitle, CommandReturn.empty]:
            query = Request(inUnitIndex=index, unit=unit, type=returned.name, data={})
            # if returned not in [CommandReturn.TITLE, CommandReturn.BULLET, CommandReturn.TABLE]:
            decision = sendDecision(data)
            if not decision : return
            elif decision == 2 : data = {}
            if not isinstance(data, dict) : data = dataclasses.asdict(data)
            query.data = data
            print(requests.post(apiUrl, json=dataclasses.asdict(query)).text)
            
        if returned in [CommandReturn.empty, CommandReturn.grid, CommandReturn.header, 
                        CommandReturn.exerciseTitle, CommandReturn.bullet, CommandReturn.title] : index += 1
        return index
    except Exception as err:
        print(err)

def interaction(tasks):
    index = 0
    while index < len(tasks):
        task = tasks[index]
        print('\nNext Task:')
        print(task)
        comm = input('Enter a command ("help" for help): ')
        splited = comm.split(' ')
        command = splited[0]
        index = handleCommand(task, command, splited, tasks, index)
        

def main():
    global unit
    unitFile = sys.argv[1]
    unit = unitFile[:-4]
    readJson('sepran-urmi.json')
    with pdfplumber.open(unitFile) as pdf:
        processed = ''
        for page in pdf.pages[:2]:
            _, chars = extractData(page)
            newChars = processChars(chars)
            processed += processData(newChars)
        print(processed)
        splited = splitTextByRegex(processed, splitTextRegex)
        merged = mergeTitles(splited)
        interaction(merged)  
   
if __name__ == '__main__':
    main()
