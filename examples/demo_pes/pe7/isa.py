from hwtypes import Enum

class Op(Enum, cache=True):
    Add  = 1
    And  = 2
    Xor  = 4
    Shft = 8

