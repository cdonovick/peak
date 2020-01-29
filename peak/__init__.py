from .register import gen_register, gen_register2
from .memory import Memory, RAM, ROM

from .peak import Peak, PeakNotImplementedError, name_outputs, family_closure, assemble, Const

#This will be removed after Magma ADT types work properly
from .peak import Enum_fc, Product_fc, Tuple_fc

from .rtl_utils import wrap_with_disassembler

