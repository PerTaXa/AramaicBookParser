from dataclasses import dataclass
import copy
from typing import List

class General:
    def className(self):
        return type(self).__name__

    def copy(self):
        return copy.deepcopy(self)

@dataclass
class Request(General):
    inUnitIndex : int
    unit : str
    type: str
    data : dict

@dataclass
class Text:
    text: str

@dataclass
class Table(General):
    headers : List[List]
    grids : List[List]
    hasSections : List[bool]

    def clear(self):
        self.headers = []
        self.grids = []
        self.hasSections = []

@dataclass
class Exercise(General):
    title: str
    table : Table

    def clear(self):
        self.title = ''
        self.table.clear()

    def isExercise(self):
        return self.title != '' or len(self.table.headers) or len(self.table.grids)

@dataclass
class AramElement:
    aram: str

@dataclass
class EngElement:
    eng: str

@dataclass
class BothElements:
    words: List[str]
    
@dataclass
class ImageElement(AramElement):
    image: str

@dataclass
class CheckAram(EngElement):
    options : List[str]