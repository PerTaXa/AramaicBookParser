import re
import numpy as np
import copy

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

def flattenList(lst):
    return [item for sublist in lst for item in sublist]

def swapPositions(list, pos1, pos2):
    list[pos1], list[pos2] = list[pos2], list[pos1]
    return list

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
    cpy = copy.deepcopy(chars)
    for arr in cpy:
        arr.append({'text': joint})
    return flattenList(cpy)

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

def filterBy(func, arr):
    return list(filter(func, arr))

def mergeNrows(arr, n):
    if n == 1: return arr
    temp = copy.deepcopy(arr)
    for i in range(0, len(temp), n):
        for j in range(1,n):
            for k in range(len(arr[i])):
                temp[i][k].extend(temp[i + j][k])
    return temp[::n]

def topDownReArrange(arr):
    return [subArr.tolist() for subArr in np.rot90(arr, k=1, axes=(0, 1))]

def flipDiagonally(arr):
    return [subArr.tolist() for subArr in np.rot90(np.fliplr(arr))]

def rearrangeByInterval(arr, n):
    res = []
    for i in range(n):
        res.extend(arr[i::n])
    return res
