import subprocess
from enum import Enum
from data_classes import *
from utils import *

commonDelimiter = 'ჭ'
exercise = Exercise('', Table([],[],[]))
table = Table([],[],[])
# tableHeaders = {
#     3row3col - 494
#     3row4col - 561
#     1row - 310
#     3row1col - 411,318
#     2row3col - 304,322,294
#     3row2col - 287
#     2row2col-272,185
# }

# Pattern
# 1 -       example
#           ex   ex
# 2 -  example    example
#      ex   ex
# 3 -  example    example    example
#                 ex   ex
# 4 -       example
#         ex  ex  ex
# 5 -  example    example
#         ex
#         ex
# 6 -  example    example
#         ex
#      ex   ex
# 7 -  example    example
#     ex     ex
#          ex   ex
# 8 - example     example    example    example   example
#                 ex   ex
         
class CommandReturn(Enum):
    listen_standart = 1
    mixed_images = 2
    all_images = 3

    matchPictures = 4
    addVowelPoints = 5

    translate_standart_engAssyr = 6
    translate_standart_assyrEng = 7
    translate_p33 = 8

    checkFromTwo = 9
    addMissingLetter = 10
    writeWordFromPic_checkFromTwo = 11

    nano = 12
    empty = 13
    title = 14
    header = 15
    grid = 16
    bullet = 17
    table = 18
    exerciseTitle = 19
    help = 20

def printHelp(*_):
    print('Commands:')
    for key in commands.keys():
        print(key, end=' ')
    print('\n')
    return CommandReturn.help, {}

def openNano(text):
    tempFile = 'temp.txt'
    with open(tempFile, 'w+') as file:
        file.write(text)
        file.close()
        subprocess.call(['nano', tempFile])
        return CommandReturn.nano, {}

def swapIfNeeded(arr, elemLines):
    if elemLines == 3:
        for col in arr:
            for elem in col:
                swapPositions(elem, 0, 1)
    return arr

def parseRows(text, columns, direction, elemLines):
    lines = filterBy(lambda elem : len(elem), text.split('\n'))
    splited = [line.split(commonDelimiter) for line in lines]
    evenSplited = [splitArrNParts(spl, columns) for spl in splited]
    elemMatched = mergeNrows(evenSplited, elemLines)
    directing = topDownReArrange(elemMatched)
    directed = flipDiagonally(directing) if direction else directing
    # result = swapIfNeeded(directed, elemLines)
    return directed

def elemToObj(arr, type):
    obj = 0
    if type == 0:
        obj = AramElement(arr[0])
    elif type == 1:
        obj = EngElement(arr[0])
    elif type == 2:
        obj = BothElement(arr[0], arr[1])
    elif type == 3:
        obj = TranslateElement(arr[0], arr[1], arr[2])
    elif type == 4:
        obj = ImageElement(arr[0], '')
    elif type == 5:
        obj = CheckAram(arr[1], [arr[0], arr[1]])
    elif type == 6:
        obj = MissingLetter('rightHere', arr[0])
    return obj
    
def convertToDataclasses(grid, type):
    result = copy.deepcopy(grid)
    for ind1, column in enumerate(grid):
        for ind2, elem in enumerate(column):
            result[ind1][ind2] = elemToObj(elem, type)
    return result


def gridParse(text, *args):
    columns = int(args[0])
    elemType = int(args[1])
    direction = int(args[2])
    elemLines = int(args[3])
    hasSections = int(args[4]) != 0
    result = parseRows(text, columns, direction, elemLines)
    result = convertToDataclasses(result, elemType)

    exercise.table.grids.append(result) if exercise.isExercise() else table.grids.append(result)
    exercise.table.hasSections.append(hasSections) if exercise.isExercise() else table.hasSections.append(hasSections)
    return CommandReturn.grid, {}

def handleHeaderPattern(text, pattern):
    lines = text.split('\n')
    if pattern == 1:
        return {
            lines[0] : lines[1].split(commonDelimiter)
        }
    elif pattern == 2:
        gr = lines[0].split(commonDelimiter)
        return {
            gr[0] : [],
            gr[1] : lines[1].split(commonDelimiter)
        }
    elif pattern == 3:
        gr = lines[0].split(commonDelimiter)
        return {
            gr[0] : [],
            gr[1] : lines[1].split(commonDelimiter),
            gr[2] : []
        }
    elif pattern == 4:
        return {
            lines[0] : lines[1].split(commonDelimiter)
        }
    elif pattern == 5:
        gr = lines[0].split(commonDelimiter)
        return {
            gr[0] : {
                lines[1] : lines[2]
            },
            gr[1] : []
        }
    elif pattern == 6:
        gr = lines[0].split(commonDelimiter)
        return {
            gr[0] : {
                lines[1] : lines[2].split(commonDelimiter)
            },
            gr[1] : []
        }
    elif pattern == 7:
        gr = lines[0].split(commonDelimiter)
        gr2 = lines[1].split(commonDelimiter)
        return {
            gr[0] : {
                gr2[0] : [],
                gr2[1] : lines[2].split(commonDelimiter)
            },
            gr[1] : []
        }
    elif pattern == 8:
        gr = lines[0].split(commonDelimiter)
        return {
            gr[0] : [],
            gr[1] : lines[1].split(commonDelimiter),
            gr[2] : [],
            gr[3] : []
        }

def headerParse(text, *args):
    pattern = int(args[0])
    grid = []
    if pattern:
        grid = handleHeaderPattern(text, pattern)
    else:
        columns = int(args[1])
        elemLines = int(args[2])
        grid = parseRows(text, columns, 0, elemLines)
        
    exercise.table.headers.append(grid) if exercise.isExercise() else table.headers.append(grid)
    return CommandReturn.header, {}

def beatifyText(text):
    text = re.sub('\n', '', text)
    text = re.sub(commonDelimiter, '', text)
    return text

def bulletParse(text):
    text = beatifyText(text)
    return CommandReturn.bullet, Text(text)

def titleParse(text):
    text = re.sub(commonDelimiter, '', text)
    return CommandReturn.title, Text(text)

def exerciseParse(text):
    text = beatifyText(text)
    exercise.title = text
    return CommandReturn.exerciseTitle, Text(text)

def saveExercise(*args):
    type = int(args[1])
    data = exercise.copy()
    exercise.clear()
    return CommandReturn(type), data

def saveTable(*_):
    data = table.copy()
    table.clear()
    print(exercise)
    print(table)
    return CommandReturn.table, data

def next(*_):
    return CommandReturn.empty, {}

commands = {
    'help' : printHelp,
    'nano' : openNano,
    'next' : next,
    'header' : headerParse,
    'grid' : gridParse,
    'bullet' : bulletParse,
    'title' : titleParse,
    'exertitle' : exerciseParse,
    'saveexer' : saveExercise,
    'savetable' : saveTable
}