from dataclasses import dataclass
from typing import List

class Parser:

    @staticmethod
    def parseTitle(text):
        titles = text.split('\n')
        return titles[0], titles[1]

    @staticmethod
    def parseBullet(text, bulletChar):
        splited = text.split(bulletChar)
        return [bulletChar + bullet for bullet in splited[1:]]

@dataclass
class Unit:
    # title: tuple(str, str)
    # bullets: List[str]

    def __init__(self, text: str, bulletChar: str) -> None:
        self.title = Parser.parseTitle(text)
        self.bullets =  Parser.parseBullet(text, bulletChar)