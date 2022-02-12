import sys
import pdfplumber
import json
from functools import cmp_to_key
from commands import *
from utils import *
import requests
import dataclasses
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
apiUrl = 'http://192.168.131.160:3030/unit-content'
splitTextRegex = '\d\).|❑|<title>'
unit = ''

mutex = Semaphore(0)
comm = ''

root = Tk()
root.configure(bg='blue')
def on_closing():
    root.destroy()
    os._exit(0)
root.protocol("WM_DELETE_WINDOW", on_closing)

def popupwin():
    top = Toplevel()
    # top.attributes('-topmost', 'true')
    top.geometry("200x150")

    entry= Entry(top)
    entry.pack()
    Button(top,text= "Load state").pack(pady= 5,side=TOP)
    Button(top, text="Load Previous state", command=lambda:top.destroy()).pack(pady=5, side= TOP)
    Button(top, text="Load default").pack(pady=5, side= TOP)

scrolledTxt = ScrolledText(root, font = ("Times New Roman",15))
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
    for i in range(len(line)):
        if line[i]['fontname'][7:] == 'Sepran':
            # if not line[i]['text'] in sepranUrmiDict: print(line[i]['text'])
            if not(i and line[i - 1]['fontname'][7:] != 'Sepran' and line[i]['text'] in '()'):
                line[i]['text'] = sepranUrmiDict[line[i]['text']] if line[i]['text'] in sepranUrmiDict else 'ყ' + line[i]['text'] + 'ყ'
            seprInd = i if seprInd == -1 else seprInd
        else:
            if line[i]['text'] in '-+': #-+.
                # line[i]['text'] = '⠀-⠀'
                line[i]['text'] = '‎' + line[i]['text']
                
            if i and line[i - 1]['fontname'][7:] == 'Sepran':
                index = i
                if line[i - 1]['text'] == ' ': index -= 1

                if isAramLetter(''.join([ch['text'] for ch in line[seprInd: index]])):
                    inserts.append(index)
                    
                line[seprInd: index] = line[seprInd: index][::-1]
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
    if abs((leftX + rightX) / 2 - pageMiddle) < 5 and leftX > pageLeftX + 12:
        line.insert(0, {'text': '<title>', 'fontname': 'HCFQDX+Century'})

    line = changeFont(line, '?', '^', 'HCFQDX+Sepran')
    line = changeFont(line, ',', '#', 'HCFQDX+Sepran')
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
            tasks[index] = scrolledTxt.get(1.0, END)
            splitIfTag(tasks, index)
               
        elif returned not in [CommandReturn.help, CommandReturn.header, CommandReturn.grid, 
                                CommandReturn.exerciseTitle, CommandReturn.empty]:
            query = Request(inUnitIndex=index, unit=unit, type=returned.name, data={})
            # if returned not in [CommandReturn.TITLE, CommandReturn.BULLET, CommandReturn.TABLE]:
            decision = sendDecision(data)
            if not decision : return index
            elif decision == 2 : data = {}
            if not isinstance(data, dict) : data = dataclasses.asdict(data)
            query.data = data
            print(requests.post(apiUrl, json=dataclasses.asdict(query)).text)
        elif returned not in [CommandReturn.empty]:
            decision = sendDecision(data)
            if not decision : return index
            elif decision == 1 : return index + 1
        
        if returned in [CommandReturn.empty, CommandReturn.grid, CommandReturn.header, 
                        CommandReturn.exerciseTitle, CommandReturn.bullet, CommandReturn.title] : index += 1
    except Exception as _:
        messagebox.showerror("Error", "Wrong Command")
        print('---  Wrong command!!!  ---')
    
    return index

def interaction(tasks):
    global scrolledTxt
    index = 0
    while index < len(tasks):
        task = tasks[index]
        print('\nNext Task:')
        scrolledTxt.delete(1.0, END)
        scrolledTxt.insert(END, task)
        print(task)
        print('Enter a command ("help" for help): ')
        mutex.acquire()
        # comm = input('Enter a command ("help" for help): ')
        splited = comm.split(' ')
        command = splited[0]
        index = handleCommand(scrolledTxt.get(1.0, END), command, splited, tasks, index)
    os._exit(0)
        
def commandFromGui(command):
    global comm
    comm = command
    mutex.release()

def main():
    global unit
    unitFile = sys.argv[1]
    unit = unitFile[:-4]
    readJson('sepran-urmi.json')

    Button(root, text="Exit", command=on_closing).grid(row=0, column=0)
    Button(root, text="Load state", command=popupwin).grid(row=1, column=0)
    Button(root, text="Next", command=lambda:commandFromGui('next')).grid(row=0, column=8)
    Button(root, text="Previous", command=lambda:messagebox.showerror("Error", "Wrong Command")).grid(row=1, column=8)
    Button(root, text="Reparse", command=lambda:commandFromGui('vim')).grid(row=2, column=8)

    Button(root, text="Bullet", command=lambda:commandFromGui('bullet')).grid(row=5, column=1)
    Button(root, text="Title", command=lambda:commandFromGui('title')).grid(row=5, column=2)
    Button(root, text="Exercise title", command=lambda:commandFromGui('exertitle')).grid(row=5, column=3)
    headerEnt= Entry(root)
    headerEnt.grid(row=4, column=4)
    Button(root, text="Header", command=lambda:commandFromGui('header ' + headerEnt.get(1.0, END))).grid(row=5, column=4)
    gridEnt= Entry(root)
    gridEnt.grid(row=4, column=5)
    Button(root, text="Grid", command=lambda:commandFromGui('grid ' + gridEnt.get(1.0, END))).grid(row=5, column=5)
    Button(root, text="SaveTable", command=lambda:commandFromGui('savetable')).grid(row=5, column=6)
    saveexerEnt= Entry(root)
    saveexerEnt.grid(row=4, column=7)
    Button(root, text="SaveExercise", command=lambda:commandFromGui('saveexer ' + saveexerEnt.get(1.0, END))).grid(row=5, column=7)

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
        Thread(target=interaction, args=(merged,)).start()
        # interaction(merged) 
        #  

    popupwin()
    root.mainloop() 
   
if __name__ == '__main__':
    main()
