from .register import gen_register, gen_register2
from .memory import Memory, RAM, ROM

from .peak import Peak, PeakNotImplementedError, Const

from .features import name_outputs, gen_input_t, gen_output_t, typecheck, assemble, family_closure

#This will be removed after Magma ADT types work properly
from .utils import Enum_fc, Product_fc, Tuple_fc

from .rtl_utils import wrap_with_disassembler

