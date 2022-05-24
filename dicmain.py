from string import *
import sys
import json
import re
from functools import cmp_to_key
from commands import *
from utils import *
import requests
import dataclasses
import numpy as np
import os

engDict = ascii_letters + punctuation
sepranUrmiDict = {}
simonSpecialChar = 'ܔ'
simonSpecial = {'text' : simonSpecialChar, 'fontname': 'HCFQDX+Sepran'}
pageWidth = 595
pageHeight = 842
pageCropTop = 100
pageMiddle = 291.4
pageLeftX = 92.771
pageRightX = 490.538
apiUrl = 'http://192.168.125.160:3030/dictionaryParser'
splitTextRegex = '\d\).|❑|<title>'
unit = ''
unitFile = ''
globIndex = 0
globTasks = []
comm = ''

@dataclass
class RequestDic(General):
    aram : str
    value : str
    left: str
    m: bool
    f: bool
    plural: str
    eng: List[str]
    eng_def: List[str]
    root: str

@dataclass
class FinalDic(General):
    value : List[RequestDic]


def readJson(file):
    global sepranUrmiDict
    with open(file, encoding='utf-8') as json_file:
        sepranUrmiDict = json.load(json_file)

def extractData(page):
    text = page.extract_text(y_tolerance=yTolerance)
    chars = page.chars
    # words = page.extract_words(extra_attrs=["fontname"])
    return text,chars

def splitPage(page):
    page1 = page.crop((0, pageCropTop, pageWidth / 2, pageHeight))
    page2 = page.crop((pageWidth / 2, pageCropTop, pageWidth, pageHeight))
    return [page1, page2]

def processRequest(request: RequestDic):
    notNeeded = '(grammar.)|(int.)'
    # print(request.value)
    task = re.sub(notNeeded, '', request.value)
    task = re.sub('\s{2,}', ' ', task)
    task = re.sub("\(\u0702", '1)', task)
    task = re.sub("\(\u0703", '2)', task)
    task = re.sub("\(\u0704", '3)', task)
    task = re.sub(" \)", ')', task)
    task = re.sub("\( ", '(', task)
    request.value = task
    task = re.sub('1\)', '',task)
    task = re.sub('2\)', '', task)
    task = re.sub('3\)', '', task)

    x = re.findall("pl\. [^\(a-z)(0-9)]+", task)
    task = re.sub("pl\. [^\(a-z)(0-9)]+", '', task)
    for el in x:
        request.plural = el[4:].strip()

    x = re.findall("m\.\s", task)
    task = re.sub("m\.\s", '', task)
    for el in x:
        request.m = True

    x = re.findall("f\.\s", task)
    task = re.sub("f\.\s", '', task)
    for el in x:
        request.f = True
    # print(task)
    x = re.findall("\(r\...[^\(\)(a-z)]+", task)
    task = re.sub("\(r\...[^\(\)(a-z)]+", '', task)
    for el in x:
        newElem = re.sub("\(|\)", '', el)
        request.root = newElem[2:].strip()

    task = re.sub("\(adj.\)|\(adv.\)|\(n.\)|\(pron.\)|\(v.\)|\(prep.\)|\(num.\)|\(gram.\)", ', ', task)

    # x = re.findall("\([^\)]+", task)
    task = re.sub("\([^\)]+", ', ', task)
    task = re.sub("\(|\)", '', task)
    # for el in x:
    #     print(el)
        # newElem = re.sub("\(|\)", '', el)
        # request.root = newElem[2:].strip()
    
    words = re.split('; |, ',task)
    for word in words:
        word = word.strip()
        if all(y.isalpha() or y.isspace() for y in word):
            if len(word) == 0: continue
            if ' ' in word and word.split(' ')[0] != 'to':
                request.eng_def.append(word)
            else:
                request.eng.append(word)
            
    
    # task = re.sub("\(r\...[^\s\((a-z)]+", '', task)
    # for el in x:
    #     newElem = re.sub("\(|\)", '', el)
    #     request.root = newElem[2:].strip()
    request.left = task
    return request

def main():
    global unit, unitFile
    unitFile = sys.argv[1]
    readJson('sepran-urmi.json')
    dictionary = []
    req = RequestDic('', '', '', False, False, '', [], [],'')
    with open('newDictionary.txt', 'w') as newDict:
        with open(unitFile, encoding='utf-16') as pdf:
            txt = pdf.read()
            for line in txt.split('\n'):
                line = line.strip()
                # print(line)
                if len(line) < 2: continue
                # if req.aram == 'ܢܵܬܵܐ':
                #     print(line)
                if line and line[0].isalpha and not line[0] in engDict:
                    
                    if '(see (' in req.value:
                        seeInd = req.value.index('(see (')
                        req.value = req.value[:seeInd + 5] + req.value[seeInd+6:] + ')'
                    if '((see' in req.value:
                        seeInd = req.value.index('((see')
                        req.value = req.value[:seeInd + 1] + req.value[seeInd+2:] + ')'
                    if '(see)' in req.value:
                        seeInd = req.value.index('(see)')
                        req.value = req.value[:seeInd + 4] + ' ' + req.value[seeInd+5:] + ')'
                    if ')see (' in req.value:
                        seeInd = req.value.index(')see (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 1:seeInd + 5] + req.value[seeInd+6:] + ')'
                    if ')see  (' in req.value:
                        seeInd = req.value.index(')see  (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 1:seeInd + 6] + req.value[seeInd+7:] + ')'
                    if ') see  (' in req.value:
                        seeInd = req.value.index(') see  (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 2:seeInd + 7] + req.value[seeInd+8:] + ')'
                    if ') see (' in req.value:
                        seeInd = req.value.index(') see (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 2:seeInd + 6] + req.value[seeInd+7:] + ')'
                    if 'see)' in req.value:
                        seeInd = req.value.index('see)')
                        seeInd1 = req.value[:seeInd].rindex('(')
                        req.value = req.value[:seeInd1 + 1] + 'see ' + req.value[seeInd1 + 1:seeInd] + req.value[seeInd + 3:]
                    if req.value.endswith(')see'):
                        seeInd = req.value.rindex('(')
                        req.value = req.value[:seeInd + 1] + 'see ' + req.value[seeInd + 1:-3]
                    if req.value.endswith('(see'):
                        seeInd = req.value[:-4].rindex('(')
                        req.value = req.value[:seeInd + 1] + 'see ' + req.value[seeInd + 2:-4] + ')'
                    
                    if req.value.endswith(')r.'):
                        seeInd = req.value.rindex('(')
                        req.value = req.value[:seeInd + 1] + 'r. ' + req.value[seeInd + 2:-2]
                    if req.value.endswith('(r.'):
                        seeInd = req.value[:-3].rindex('(')
                        req.value = req.value[:seeInd + 1] + 'r. ' + req.value[seeInd + 1:-3] + ')'
                    if ')r. (' in req.value:
                        seeInd = req.value.index(')r. (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 1:seeInd + 4] + req.value[seeInd+5:] + ')'
                    if ') r. (' in req.value:
                        seeInd = req.value.index(') r. (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 2:seeInd + 5] + req.value[seeInd+6:] + ')'
                    if '(r. (' in req.value:
                        seeInd = req.value.index('(r. (')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 1:seeInd + 4] + req.value[seeInd+5:] + ')'
                    if '(r.)' in req.value:
                        seeInd = req.value.index('(r.)')
                        req.value = req.value[:seeInd] + '(' + req.value[seeInd + 1:seeInd + 3] + req.value[seeInd+4:] + ')'
                    if 'r.)' in req.value:
                        seeInd = req.value.index('r.)')
                        seeInd1 = req.value[:seeInd].rindex('(')
                        req.value = req.value[:seeInd1 + 1] + 'r. ' + req.value[seeInd1 + 1:seeInd] + ')' + req.value[seeInd + 3:]

                    # print(req.value)
                    req = processRequest(req)
                    dictionary.append(req)
                    req = RequestDic('', '', '', False, False, '', [], [],'')
                    for ind, char in enumerate(line):
                        if char == ' ' and ind:
                            if ind + 1 < len(line) and (line[ind + 1] in engDict or line[ind + 1] == ' '):
                                req.aram = line[:ind].strip()
                                req.aram = re.sub("\([^\)]+", '', req.aram)
                                req.aram = req.aram.strip()

                                req.value = line[ind + 1:].strip()
                                # if req.aram == 'ܢܵܬܵܐ':
                                #     print(line)
                                break
                            # else:
                                # req.aram = line[:ind-1].strip()
                                # break    
                else:
                    req.value += ' ' + line.strip()
            for reque in dictionary:
                newDict.write(reque.aram + ' ' + reque.value + '\n')

            for i in range(0, len(dictionary), 100):
                finalReq = FinalDic(dictionary[i:i+100])
                print(requests.post(apiUrl, json=dataclasses.asdict(finalReq)).text)
   
if __name__ == '__main__':
    main()
