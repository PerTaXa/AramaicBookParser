import re
import numpy as np

yTolerance = 5

def charY(char):
    return (char['bottom'] + char['top']) / 2

def sameY(char1, char2):
    return abs(charY(char1) - charY(char2)) <= yTolerance

def pageSortCmp(first, second):
        firstY = charY(first)
        secondY = charY(second)
        if sameY(first, second):
            return first['x0'] - second['x0']
        else:
            return firstY - secondY

def splitArrNParts(a, n):
    return [list(i) for i in np.array_split(a, n)]

def splitCharsBy(chars, splitter):
    res = []
    temp = []
    for mp in chars:
        if mp['text'] == splitter:
            res.append(temp)
            temp = []
        else:
            temp.append(mp)
    return res

def joinCharsBy(chars, joint):
    copy = chars.copy()
    for arr in copy:
        arr.append({'text': joint})
    return [item for sublist in copy for item in sublist]

def splitTextByRegex(text, regex):
    found = re.findall(regex, text)
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
