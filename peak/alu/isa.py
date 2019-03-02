from dataclasses import dataclass
from .. import Bits, Enum, Product

Data = Bits(16)

class ALUOP(Enum):
    Add = 0
    Sub = 2
    Or = 4
    And = 5
    XOr = 7

@dataclass
class Inst(Product):
    alu:ALUOP=ALUOP.Add
