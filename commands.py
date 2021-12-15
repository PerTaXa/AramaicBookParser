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

def tableParse(text):
    pass

def gridParse(text, *args):
    cols = int(args[0])
    lines = text.split('\n')
    splited = [line.split(commonDelimiter) for line in lines]
    evenSplited = [splitArrNParts(spl, cols) for spl in splited]
    print(evenSplited)


def simpleParse(text):
    pass

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