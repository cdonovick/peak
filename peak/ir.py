from collections import namedtuple
import typing as tp
from hwtypes.adt import Product
from hwtypes import AbstractBitVector, AbstractBit, BitVector, Bit
from .peak import Peak, name_outputs
import itertools as it

def _get_type_str(atype):
    if issubclass(atype,AbstractBitVector):
        return f"BitVector[{atype.size}]"
    elif issubclass(atype,AbstractBit):
        return "Bit"
    else:
        raise NotImplementedError(str(atype))
    #For now limit it to bitvector/bit

class IR:
    def __init__(self):
        #Stores a list of instructions (name : family_closure)
        self.instructions = {}

    def add_instruction(self,name,peak_class : Peak):
        if name in self.instructions:
            raise ValueError(f"{name} is already an existing instruction")
        self.instructions[name] = peak_class.rebind(BitVector.get_family())

    def add_peak_instruction(self, name : str, input_interface : Product, output_interface : Product, fun : tp.Callable):
        inputs = input_interface.field_dict
        outputs = output_interface.field_dict

        def ts(n):
            assert n>0
            return "".join(["    " for _ in range(n)])
        t_to_tname = {}
        idx = 0
        for t in it.chain(inputs.values(),outputs.values()):
            if not t in t_to_tname:
                t_to_tname[t] = f"t{idx}"
                idx +=1
        class_src = ""
        #for t,tname in t_to_tname.items():
        #    class_src += f"{tname}={_get_type_str(t)}\n"
        class_src += f"class {name}(Peak):\n"
        output_types = ", ".join([f"{field} = {t_to_tname[t]}" for field,t in outputs.items()])
        input_types = ", ".join([f"{field} : {t_to_tname[t]}" for field,t in inputs.items()])
        fun_call = ", ".join(inputs.keys())
        class_src += f"{ts(1)}@name_outputs({output_types})\n"
        class_src += f"{ts(1)}def __call__(self, {input_types}):\n"
        class_src += f"{ts(2)}return _fun_({fun_call})\n"
        exec_ls = {}
        #add all the types to globals
        exec_gs = {tname:t for t,tname in t_to_tname.items()}
        exec_gs.update(dict(
            BitVector=BitVector,
            Bit=Bit,
            Peak=Peak,
            name_outputs=name_outputs,
            _fun_=fun
        ))
        exec(class_src,exec_gs,exec_ls)
        cls = exec_ls[name]
        #Need to manually add the source and the environment
        cls._env_ = exec_gs
        cls._srccode_ = class_src
        cls._file_ = "ir.py"
        self.add_instruction(name,cls)

