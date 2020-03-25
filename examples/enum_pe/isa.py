from .alu import ALU_t, Signed_t
from peak import Const, family_closure
from hwtypes import Tuple, Product
import magma as m


@family_closure
def Inst_fc(family):
    Data = family.BitVector[16]
    Bit = family.Bit

    class Inst(Product):
        alu= ALU_t
        signed= Signed_t 

    return Inst