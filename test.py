from enum import Enum

mp = {
    'A' : 'ܐ',
    '´' : 'ܬ',
    'Â' : 'ܝ',
    'i' : 'ܫ'
}

a = 'ܫܬܝܐ'
b = "AÂ´i"

print((''.join([mp[ch] for ch in b[::-1]]))[::-1])

mp = {
    'mesto': {
        'mnoj' : [],
        'edit' : {
            'jensk' : [],
            'mujsk' : []
        }
    }
    
}