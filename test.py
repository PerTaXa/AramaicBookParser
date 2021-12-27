from enum import Enum

mp = {
    'A' : 'ܐ',
    '´' : 'ܬ',
    'Â' : 'ܝ',
    'i' : 'ܫ'
}

a = 'ܬܹ̈'
trs = [i.isalpha() for i in a]
print(trs.count(True))

mp = {
    'mesto': {
        'mnoj' : [],
        'edit' : {
            'jensk' : [],
            'mujsk' : []
        }
    }
    
}