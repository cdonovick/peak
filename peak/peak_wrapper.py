from .family import *
import hwtypes
import inspect
import os
import logging

from peak import Peak, family_closure
from peak import family
from peak.family import AbstractFamily
from hwtypes import Tuple


def exec_source(source, name, globals):
    path = ".ast_tools"
    file_name = os.path.join(path, f"{name}.py")
    print(file_name)
    os.makedirs(path, exist_ok=True)
    with open(file_name, 'w') as fp:
        fp.write(source)
    try:
        code = compile(source, filename=file_name, mode='exec')
    except Exception as e:
        logging.exception("Error compiling source")
        raise e from None
    _locals = {}
    try:
        exec(code, globals, _locals)
    except Exception as e:
        logging.exception("Error executing code")
        raise e from None

    #Need to write out a file, then exec using 'compile'
    return _locals[name]

def wrap_peak_class(PE_fc):
    inputs = PE_fc.Py.input_t
    outputs = PE_fc.Py.output_t

    new_inputs = {}

    instr_name = 'inst'
    instr_type = inputs.field_dict['inst']

    new_inputs[instr_name] = inputs[instr_name]
    new_inputs_str = "inst : Inst, "

    tuple_inputs_str = ""
    constructed_tuples = ""

    pe_call_inputs = "inst, "

    for name, type_ in inputs.field_dict.items(): 
        if name != instr_name:

            if issubclass(type_, hwtypes.Tuple):
                tuple_inputs_str += "    " + name + "_tuple_t = Tuple["
                pe_call_inputs += name + "_constructed, "
                constructed_tuples += name + "_constructed = " + name + "_constructor(*["

                for ind, i in enumerate(inputs[name]):
                    if issubclass(i, hwtypes.BitVector):
                        new_inputs[name + str(ind)] = "Data"
                        new_inputs_str += name + str(ind) + " : Data, "
                        tuple_inputs_str += "Data, "
                        width = len(i)
                    else:
                        new_inputs[name + str(ind)] = "Bit"
                        new_inputs_str += name + str(ind) + " : Bit, "
                        tuple_inputs_str += "Bit, "

                    constructed_tuples += name + str(ind) + ", "

                tuple_inputs_str = tuple_inputs_str[:-2]
                tuple_inputs_str += "]\n    "+name+"_constructor = family.get_constructor("+name+"_tuple_t)\n"
                constructed_tuples = constructed_tuples[:-2]
                constructed_tuples += "])\n            "
            else:
                if issubclass(type_, hwtypes.BitVector):
                    new_inputs[name] = "Data"
                    new_inputs_str += name + " : Data, "
                    width = len(type_)
                else:
                    new_inputs[name] = "Bit"
                    new_inputs_str += name + " : Bit, "
                pe_call_inputs += name + ", "

    pe_call_inputs = pe_call_inputs[:-2]
    new_inputs_str = new_inputs_str[:-2]


    outputs_str = ""
    outputs_type_str = ""
    new_outputs_str = ""
    outputs_expanded = ""

    for idx, (name, type_) in enumerate(outputs.field_dict.items()): 
        
        if issubclass(type_, hwtypes.Tuple):
            outputs_type_str += "out" + str(name) + ", "
            
            for ind, i in enumerate(outputs[name]):
                if issubclass(i, hwtypes.BitVector):
                    outputs_str += "Data, "
                    out_width = len(i)
                else:
                    outputs_str += "Bit, "
                outputs_expanded += f"out{idx}[{ind}], "
        elif issubclass(type_, hwtypes.BitVector):
            outputs_str += "Data, "
            outputs_type_str += "out" + str(idx) + ", "
            outputs_expanded += f"out{idx}, "
        else:
            outputs_str += "Bit, "
            outputs_type_str += "out" + str(idx) + ", "
            outputs_expanded += f"out{idx}, "
            

    outputs_str = outputs_str[:-2]
    outputs_type_str = outputs_type_str[:-2]
    outputs_expanded = outputs_expanded[:-2]

    new_peak_class = '''
@family_closure
def PE_wrapped_fc(family: AbstractFamily):
    Data = family.BitVector['''+ str(width) +''']
    Bit = family.Bit
    # Inst = Inst_fc(family)
''' + tuple_inputs_str + '''
    @family.assemble(locals(), globals())
    class PE_wrapped(Peak):
        def __init__(self):
            self.PE : PE_fc(family) = PE_fc(family)()

        def __call__(self, ''' + new_inputs_str + ''') -> (''' + outputs_str + '''):
            ''' + constructed_tuples + '''
            ''' + outputs_type_str + ''' = self.PE(''' + pe_call_inputs + ''')
            return ''' + outputs_expanded + '''
    
    return PE_wrapped

'''
    print(new_peak_class)
    _globals = dict(
        Peak=Peak,
        AbstractFamily=AbstractFamily,
        family_closure=family_closure,
        family=family,
        # Inst_fc=Inst_fc,
        Inst=Inst,
        PE_fc=PE_fc,
        Tuple=Tuple
    )

    return exec_source(new_peak_class, "PE_wrapped_fc", _globals)