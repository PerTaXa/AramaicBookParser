from enum import Enum

import re

txt = '(r. ܲܪܸܨ)'
x = re.findall("\(r\...[^\s\(\)(a-z)]+", txt)
print(x)

# txt = '(r.      (ܬܵܒܹܪܬܲܓܒܘܼܪܹܐ (v.)'
# x = re.sub('\s{2,}', ' ', txt)
# print(x)