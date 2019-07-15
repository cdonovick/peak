from collections import namedtuple
import typing as tp
from hwtypes.adt import Product
from hwtypes import AbstractBitVector, AbstractBit
from .peak import Peak, name_outputs
import itertools as it

def _get_type_str(atype):
    if issubclass(atype,AbstractBitVector):
        return f"family.BitVector[{atype.size}]"
    elif issubclass(atype,AbstractBit):
        return "family.Bit"
    else:
        raise NotImplementedError(str(atype))
    #For now limit it to bitvector/bit

class IR:
    def __init__(self):
        #Stores a list of instructions (name : family_closure)
        self.instructions = {}

    def add_instruction(self,name,family_closure : tp.Callable):
        if name in self.instructions:
            raise ValueError(f"{name} is already an existing instruction")
        self.instructions[name] = family_closure

    def add_peak_instruction(self, name : str, input_interface : Product, output_interface : Product, fun : tp.Callable):
        inputs = input_interface.field_dict
        outputs = output_interface.field_dict

        def ts(n):
            assert n>0
            return "".join(["    " for _ in range(n)])
        fc_str = "def family_closure(family):\n"
        t_to_tname = {}
        idx = 0
        for t in it.chain(inputs.values(),outputs.values()):
            if not t in t_to_tname:
                t_to_tname[t] = f"t{idx}"
                idx +=1
        for t,tname in t_to_tname.items():
            fc_str += f"{ts(1)}{tname}={_get_type_str(t)}\n"
        fc_str += f"{ts(1)}class {name}(Peak):\n"
        output_types = ", ".join([f"{field} = {t_to_tname[t]}" for field,t in outputs.items()])
        input_types = ", ".join([f"{field} : {t_to_tname[t]}" for field,t in inputs.items()])
        fun_call = ", ".join(inputs.keys())
        fc_str += f"{ts(2)}@name_outputs({output_types})\n"
        fc_str += f"{ts(2)}def __call__(self, {input_types}):\n"
        fc_str += f"{ts(3)}return _fun_({fun_call})\n"
        fc_str += f"{ts(1)}return {name}\n"
        exec_ls = {}
        exec_gs = dict(Peak=Peak,name_outputs=name_outputs,_fun_=fun)
        exec(fc_str,exec_gs,exec_ls)
        self.add_instruction(name,exec_ls["family_closure"])

