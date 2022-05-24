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
from tkinter import *
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from threading import Semaphore, Thread
import os

sepranUrmiDict = {}
simonSpecialChar = 'ܔ'
simonSpecial = {'text' : simonSpecialChar, 'fontname': 'HCFQDX+Sepran'}
pageWidth = 595.275
pageHeight = 841.890
pageCropTop = 170
pageMiddle = 291.4
pageLeftX = 92.771
pageRightX = 490.538
apiUrl = 'http://192.168.43.160:3030/unit-content'
splitTextRegex = '\d\).|❑|<title>'
unit = ''
unitFile = ''
globIndex = 0
globTasks = []
loadStatePopUp = None
comm = ''

root = Tk()
root.configure(bg='blue')
def on_closing():
    print('Save state?')
    if messagebox.askyesno('State', 'Save this state?'):
        with open("{}.json".format(unit), "w") as f:
            # jsonstr = json.dumps(tasks)
            stateData = {
                'index':globIndex,
                'data':globTasks
            }
            json.dump(stateData, f)
    root.destroy()
    os._exit(0)

root.protocol("WM_DELETE_WINDOW", on_closing)

scrolledTxt = ScrolledText(root, font = ("TkFixedFont",15), height=15)
scrolledTxt.grid(row=0, column=1, rowspan=3, columnspan=7)

def readJson(file):
    global sepranUrmiDict
    with open(file, encoding='utf-8') as json_file:
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

    # print(''.join([char['text'] for char in newChars]))
    return newChars

def convertToAramaic(line):
    seprInd = -1
    inserts = []
    prevFont = ''
    for i in range(len(line)):
        # if line[i]['text'] == '"':
        #     print(line[i]['fontname'])
        
        if line[i]['text'] in '.?:,[]+-"' and prevFont and line[i]['fontname'][7:]:
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

            if prevFont[7:] == 'Sepran' and seps > 0:
                line[i]['fontname'] = 'HCFQDX+Sepran'
                if line[i]['text'] == ',':
                    line[i]['text'] = '#'
                elif line[i]['text'] == '+':
                    line[i]['text'] = '\u0e2e'
                elif line[i]['text'] == '-':
                    line[i]['text'] = '\u0e2d'

            else:
                line[i]['fontname'] = 'HCFQDX+Century'

            prevFont = ''

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
            prevFont = line[i]['fontname']

    if seprInd != -1: 
        if isAramLetter(''.join([ch['text'] for ch in line[seprInd:]])):
            line.insert(seprInd, simonSpecial)
        line[seprInd:] = line[seprInd:][::-1]
    
    for i in range(len(inserts)):
        line.insert(inserts[i]+i, simonSpecial)

    return line

def correction(line):
    lineRepr = ''.join([ch['text'] for ch in line])
    words = lineRepr.split('ჭ')
    for i in range(len(words)):
        fraze = words[i].split(' ')
        for fr in range(len(fraze)):

            if (len(fraze[fr]) == 1 and isAramLetter(fraze[fr])) or (fr < len(fraze) - 1 and fraze[fr + 1] == '-'):
                fraze[fr] = fraze[fr] + simonSpecialChar  
        words[i] = ' '.join(fraze)
    newLineRepr = 'ჭ'.join(words)
    # ind = 0
    # newLineOff = 0
    # while ind < len(lineRepr) and ind + newLineOff < len(newLineRepr):
    #     if lineRepr[ind] != newLineRepr[ind + newLineOff]:
    #         line.insert(ind + newLineOff, simonSpecial)
    #         newLineOff+=1
    #     else:
    #         ind+=1
    return newLineRepr

def processLine(line):
    leftX = float(line[0]['x0'])
    rightX = float(line[-1]['x1'])
    if abs((leftX + rightX) / 2 - pageMiddle) < 5 and leftX > pageLeftX + 12:
        line.insert(0, {'text': '<title>', 'fontname': 'HCFQDX+Century'})

    line = changeFont(line, '?', '^', 'HCFQDX+Sepran')
    line = changeFont(line, ' ', ' ', 'HCFQDX+Sepran')
    # line = changeFont(line, ',', '#', 'HCFQDX+Sepran')
    # line = changeFont(line, '+', '\u0e2e', 'HCFQDX+Sepran')
    # line = changeFont(line, '-', '\u0e2d', 'HCFQDX+Sepran')
    # line = changeFont(line, ".", '@', 'HCFQDX+Sepran')
    # line = changeFont(line, '.', '@', 'HCFQDX+Sepran')
    aramaic = convertToAramaic(line)
    aramaic = correction(aramaic)
    return aramaic

def processData(chars):
    splited = splitCharsBy(chars, '\n')
    proccessedLines = [processLine(line) for line in splited]
    
    # joined = joinCharsBy(proccessedLines, '\n')
    return '\n'.join(proccessedLines)

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
    if messagebox.askyesno('Send this data?', data):
        return 1
    else:
        return 0
    # return int(input('Enter 0, 1, 2: '))

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
            # tasks[index] = scrolledTxt.get(1.0, END)
            # splitIfTag(tasks, index)
               
        elif returned not in [CommandReturn.help, CommandReturn.header, CommandReturn.grid, 
                                CommandReturn.exerciseTitle, CommandReturn.empty, CommandReturn.prev]:
            
            if returned not in [CommandReturn.title, CommandReturn.bullet, CommandReturn.table]:
                query = Request(inUnitIndex=index-1, ascUnitName=unit, type=returned.name, data={})
            else:
                query = Request(inUnitIndex=index, ascUnitName=unit, type=returned.name, data={})
            decision = sendDecision(data)
            if not decision : return index
            elif decision == 2 : data = {}
            if not isinstance(data, dict) : data = dataclasses.asdict(data)
            query.data = data
            print(requests.post(apiUrl, json=dataclasses.asdict(query), headers={'access_token' : 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7Il9pZCI6IjYyNmY4MGMzOTIzNmJmOWRkYWQ5NWQ4NSIsInJvbGUiOiJBRE1JTiJ9LCJpYXQiOjE2NTE0ODk5MDcsImV4cCI6MTY1NDA4MTkwN30.bWIxUxXD5RQLy9uz0XXiIxIhLoc23xP--H1QZlpLmIg'}).text)
        elif returned not in [CommandReturn.empty, CommandReturn.prev]:
            decision = sendDecision(data)
            if not decision : return index
            elif decision == 1 : return index + 1
        
        if returned in [CommandReturn.empty, CommandReturn.grid, CommandReturn.header, 
                        CommandReturn.exerciseTitle, CommandReturn.bullet, CommandReturn.title] : index += 1
        if returned in [CommandReturn.prev]: index = max(index - 1, 0)
    except Exception as _:
        messagebox.showerror("Error", "Wrong Command")
        print('---  Wrong command!!!  ---')
    
    return index

def interaction(tasks, index = 0):
    global scrolledTxt, globTasks, globIndex
    # try:
    if index < len(tasks):
        globTasks = tasks
        globIndex = index

        task = tasks[index]
        print('\nNext Task:')
        scrolledTxt.delete(1.0, END)
        scrolledTxt.insert(END, task)
        print(task)
        print('Enter a command ("help" for help): ')
    else:
        os._exit(0)

def loadingState(load = 0):
    global loadStatePopUp
    print(load)
    if load == -2:
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
            loadStatePopUp.destroy()
            Thread(target=interaction, args=(merged,)).start()
            # interaction(merged) 
    else:
        with open("{}.json".format(unit), "r") as f:
                # jsonstr = json.dumps(tasks)
                stateData = json.load(f)
                prevInd = stateData['index']
                arr = stateData['data']
                finalInd = prevInd if load == -1 else load
                loadStatePopUp.destroy()
                Thread(target=interaction, args=(arr,finalInd,)).start()
                # interaction(arr, finalInd)
                # json.dump(tasks, f)
        
def commandFromGui(command):
    global globIndex, globTasks,comm
    comm = command

    splited = comm.split(' ')
    command = splited[0]

    # scrolledTxt.get(1.0, END)
    globIndex = handleCommand(globTasks[globIndex], command, splited, globTasks, globIndex)
    interaction(globTasks, globIndex)

def popupwin():
    global loadStatePopUp
    loadStatePopUp = Toplevel()
    # top.attributes('-topmost', 'true')
    loadStatePopUp.geometry("200x150")

    entry= Entry(loadStatePopUp)
    entry.insert(END, "0")
    entry.pack()
    Button(loadStatePopUp,text= "Load state", command=lambda:loadingState(int(entry.get()))).pack(pady= 5,side=TOP)
    Button(loadStatePopUp, text="Load Previous state", command=lambda:loadingState(-1)).pack(pady=5, side= TOP)
    Button(loadStatePopUp, text="Load default", command=lambda:loadingState(-2)).pack(pady=5, side= TOP)

def main():
    global unit, unitFile
    unitFile = sys.argv[1]
    unit = unitFile[:-4]
    readJson('sepran-urmi.json')

    Button(root, text="Exit", command=on_closing).grid(row=0, column=0)
    Button(root, text="Load state", command=popupwin).grid(row=1, column=0)
    Button(root, text="Next", command=lambda:commandFromGui('next')).grid(row=0, column=8)
    Button(root, text="Previous", command=lambda:commandFromGui('prev')).grid(row=1, column=8)
    Button(root, text="Edit", command=lambda:commandFromGui('vim')).grid(row=2, column=8)

    Button(root, text="Bullet", command=lambda:commandFromGui('bullet')).grid(row=5, column=1)
    Button(root, text="Title", command=lambda:commandFromGui('title')).grid(row=5, column=2)
    Button(root, text="Exercise title", command=lambda:commandFromGui('exertitle')).grid(row=5, column=3)
    Label(root, text="Header type / columns / element lines").grid(row=3, column=4)
    headerEnt= Entry(root)
    headerEnt.grid(row=4, column=4)
    Button(root, text="Header", command=lambda:commandFromGui('header ' + headerEnt.get())).grid(row=5, column=4)

    Label(root, text="Columns/direction/elemLines/hassection").grid(row=3, column=5)
    gridEnt= Entry(root)
    gridEnt.grid(row=4, column=5)
    Button(root, text="Grid", command=lambda:commandFromGui('grid ' + gridEnt.get())).grid(row=5, column=5)
    Label(root, text="1: AramElement\n2: EngElement\n3: BothElements\n4: ImageElement\n5: CheckAram").grid(row=6, column=5)

    Button(root, text="SaveTable", command=lambda:commandFromGui('savetable')).grid(row=5, column=6)

    Label(root, text="ExerciseType").grid(row=3, column=7)
    variable = StringVar(root)
    variable.set(exerciseTypes[0]) # default value
    saveexerEnt = OptionMenu(root, variable, *exerciseTypes)
    saveexerEnt.grid(row=4, column=7)
    Button(root, text="SaveExercise", command=lambda:commandFromGui('saveexer ' + str(exerciseTypes.index(variable.get())))).grid(row=5, column=7)

    # with pdfplumber.open(unitFile) as pdf:
    #     processed = ''
    #     for page in pdf.pages:
    #         _, chars = extractData(page)
    #         newChars = processChars(chars)
    #         processed += processData(newChars)
    #     # print(processed)
    #     splited = splitTextByRegex(processed, splitTextRegex)
    #     merged = mergeTitles(splited)
    #     merged.append('The End 🔥')
    #     Thread(target=interaction, args=(merged,)).start()
    #     # interaction(merged) 
    #     #  

    popupwin()
    root.mainloop() 
   
if __name__ == '__main__':
    main()
