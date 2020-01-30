from peak import Enum_fc
from functools import lru_cache

@lru_cache(None)
def Op_fc(family):
    Enum = Enum_fc(family)
    class Op(Enum):
        Add  = 1
        And  = 2
        Xor  = 4
        Shft = 8
    return Op
