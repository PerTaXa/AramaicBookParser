import subprocess
from enum import Enum
from data_classes import *
from utils import *

commonDelimiter = 'ჭ'

class CommandReturn(Enum):
    NANO = 1
    NEXT = 2

def printHelp(*_):
    print('Commands:')
    for key in commands.keys():
        print(key, end=' ')
    print('\n')

# def toUnit(text, bulletChar = '❑'):
#     print(Unit(text, bulletChar))
#     return CommandReturn.NEXT

def openNano(text):
    tempFile = 'temp.txt'
    with open(tempFile, 'w+') as file:
        file.write(text)
        file.close()
        subprocess.call(['nano', tempFile])
        return CommandReturn.NANO

def swapIfNeeded(arr, elemLines):
    if elemLines == 3:
        for col in arr:
            for elem in col:
                swapPositions(elem, 0, 1)
    return arr

def tableParse(text, *args):
    columns = int(args[0])
    headerRows = int(args[1])
    headerArr = []
    for i in range(headerRows):
        temp = []
        num = int(args[2 + 2*i])
        for j in range(num):
            temp.append(args[2 + 2*i + j])
        headerArr.append((num, temp))
    print(headerArr)

def gridParse(text, *args):
    columns = int(args[0])
    direction = int(args[1])
    elemLines = int(args[2])
    lines = filterBy(lambda elem : len(elem), text.split('\n'))
    splited = [line.split(commonDelimiter) for line in lines]
    evenSplited = [splitArrNParts(spl, columns) for spl in splited]
    elemMatched = mergeNrows(evenSplited, elemLines)
    directing = topDownReArrange(elemMatched)
    directed = flipDiagonally(directing) if direction else directing
    swapped = swapIfNeeded(directed, elemLines)
    return swapped

def simpleParse(text):
    return text

def next(*_):
    return CommandReturn.NEXT

commands = {
    'help' : printHelp,
    # 'unit' : toUnit,
    'nano' : openNano,
    'next' : next,
    'table' : tableParse,
    'grid' : gridParse,
    'simple' : simpleParse
}