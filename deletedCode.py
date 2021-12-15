# def processData(chars):
#     charsInd = 0
#     proccessed = ''

#     for textChar in text:
#         if textChar != chars[charsInd]['text']:
#             proccessed += textChar
#         else:
#             # if charsInd and chars[charsInd]['x0'] > 150 and abs(charY(chars[charsInd - 1]) - charY(chars[charsInd])) > 10:
#             #     proccessed += '<title>'
#             #     proccessed += textChar
#             if chars[charsInd]['fontname'][7:] == 'Sepran':
#                 # txt += 'ჭ'
#                 proccessed += textChar
#             else:
#                 proccessed += textChar
#             charsInd += 1

#     charebi = ''
#     for i in newChars:
#         charebi += i['text']
#     print(charsInd, len(chars))
#     print(charebi == text)
#     print(charebi)
#     print(text)
#     return proccessed