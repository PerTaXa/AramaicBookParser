import subprocess
from enum import Enum
from data_classes import *

class CommandReturn(Enum):
    NANO = 1
    NEXT = 2

def printHelp(*_):
    print('Commands:')
    for key in commands.keys():
        print(key, end=' ')
    print('\n')

def toUnit(text, bulletChar = '❑'):
    print(Unit(text, bulletChar))
    return CommandReturn.NEXT

def openNano(text):
    tempFile = 'temp.txt'
    with open(tempFile, 'w+') as file:
        file.write(text)
        file.close()
        subprocess.call(['nano', tempFile])
        return CommandReturn.NANO

def next(*_):
    return CommandReturn.NEXT

commands = {
    'help' : printHelp,
    'unit' : toUnit,
    'nano' : openNano,
    'next' : next
}