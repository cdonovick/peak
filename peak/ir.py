from collections import namedtuple
import typing as tp
from hwtypes.adt import Product
from hwtypes import AbstractBitVector, AbstractBit, BitVector, Bit
from .peak import Peak
from .features import name_outputs, family_closure
import itertools as it
from hwtypes.adt_util import rebind_type

_TAB_SIZE = 4
class IR:
    def __init__(self):
        #Stores a list of instructions (name : family_closure)
        self.instructions = {}

    def add_instruction(self, name, peak_fc : tp.Callable):
        if name in self.instructions:
            raise ValueError(f"{name} is already an existing instruction")
        self.instructions[name] = peak_fc

    #fun should have the form def fun(family, *args)
    def add_peak_instruction(self, name : str, input_interface : Product, output_interface : Product, fun : tp.Callable, cls_name=None):
        if cls_name is None:
            cls_name = name
        #Assuming for now that abstract bitvectors are used in the interfaces
        inputs = input_interface.field_dict
        outputs = output_interface.field_dict
        tab = ' '*_TAB_SIZE
        t_to_tname = {}
        idx = 0
        for t in it.chain(inputs.values(), outputs.values()):
            if not t in t_to_tname:
                t_to_tname[t] = f"t{idx}"
                idx +=1
        class_src = [f"@_family_closure"]
        class_src.append(f"def peak_fc(family):")
        for t, tname in t_to_tname.items():
            class_src.append(f"{tab*1}_{tname} = {tname}")
        class_src.append(f"{tab*1}class {cls_name}(Peak):")
        output_types = ", ".join([f"{field} = _{t_to_tname[t]}" for field, t in outputs.items()])
        input_types = ", ".join([f"{field} : _{t_to_tname[t]}" for field, t in inputs.items()])
        fun_call = "family, " + ", ".join(inputs.keys())
        class_src.append(f"{tab*2}@name_outputs({output_types})")
        class_src.append(f"{tab*2}def __call__(self, {input_types}):")
        class_src.append(f"{tab*3}return _fun_({fun_call})")
        class_src.append(f"{tab*1}return {cls_name}")
        class_src = '\n'.join(class_src)
        exec_ls = {}
        #add all the types to globals
        exec_gs = {tname:t for t, tname in t_to_tname.items()}
        exec_gs.update(dict(
            Peak=Peak,
            name_outputs=name_outputs,
            _fun_=fun,
            _family_closure=family_closure
        ))
        exec(class_src, exec_gs, exec_ls)
        peak_fc = exec_ls["peak_fc"]
        self.add_instruction(name, peak_fc)

