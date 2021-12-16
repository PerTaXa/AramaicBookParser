import numpy as np

def topDownReArrange(arr):
    return [subArr.tolist() for subArr in np.rot90(arr, k=1, axes=(0, 1))]

def flipDiagonally(arr):
    return [subArr.tolist() for subArr in np.rot90(np.fliplr(arr))]

ar = [[1,2,3], 
    [4,5,6],
    [7,8,9]]
print(topDownReArrange(ar))
print(flipDiagonally(ar))

mp = {
    'mesto': {
        'mnoj' : [],
        'edit' : {
            'jensk' : [],
            'mujsk' : []
        }
    }
    
}