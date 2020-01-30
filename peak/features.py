from collections import OrderedDict
from hwtypes.adt import Product, Tuple
import functools
from ast_tools.passes import begin_rewrite, end_rewrite
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
from ast_tools.stack import SymbolTable
from hwtypes import SMTBit
from peak.assembler import Assembler
import magma

def name_outputs(**outputs):
    """Decorator meant to apply to any function to specify output types
    The output type will be stored in fn._peak_outputs__
    The input type will be stored in fn._peak_inputs_
    Will verify that all the inputs have type annotations
    Will also verify that the outputs of running fn will have the correct number of bits
    """
    peak_outputs = OrderedDict()
    for oname, otype in outputs.items():
        peak_outputs[oname] = otype
    output_t = Product.from_fields("Output", peak_outputs)
    def decorator(call_fn):
        call_fn._output_t = output_t
        return call_fn
    return decorator

def gen_input_t(call_fn):
    if hasattr(call_fn, "_input_t"):
        return call_fn

    #construct input_t
    arg_offset = 1 if call_fn.__name__ == "__call__" else 0
    peak_inputs = OrderedDict()
    num_inputs = call_fn.__code__.co_argcount
    input_names = call_fn.__code__.co_varnames[arg_offset:num_inputs]
    in_types = call_fn.__annotations__
    in_type_keys = set(in_types.keys())
    # Remove return annotation if it exists
    if "return" in in_type_keys:
        in_type_keys.remove("return")
    if set(input_names) != set(in_type_keys):
        raise ValueError(f"Missing type annotations on inputs: {set(input_names)} != {set(in_type_keys)}")
    for name in input_names:
        input_type= in_types[name]
        peak_inputs[name] = in_types[name]

    #Just set input_t to None if there are no inputs
    if len(peak_inputs) == 0:
        input_t = None #Empty 
    else:
        input_t = Product.from_fields("Input", peak_inputs)

    call_fn._input_t = input_t
    return call_fn

def gen_output_t(call_fn):
    if hasattr(call_fn, "_output_t"):
        return call_fn

    try:
        output_types = call_fn.__annotations__['return']
    except KeyError:
        raise ValueError(f"Missing output type annotations on __call__ {call_fn}")
    except AttributeError:
        raise ValueError(f"Missing definition for __call__ {call_fn}")
    if output_types is None:
        output_t = None
    else:
        if not isinstance(output_types, tuple):
            output_types = (output_types,)
        output_t = Tuple[output_types]
    call_fn._output_t = output_t
    return call_fn

def typecheck(call_fn):
    if not hasattr(call_fn, "_output_t"):
        raise ValueError("Need to use gen_output_t for typechecking")
    output_t = call_fn._output_t
    @functools.wraps(call_fn)
    def call_wrapper(*args, **kwargs):
        results = call_fn(*args, **kwargs)
        single_output = not isinstance(results, tuple)
        if single_output:
            results = (results,)
        for i, (oname, otype) in enumerate(output_t.field_dict.items()):
            if not isinstance(results[i], otype):
                raise TypeError(f"result type for output {oname} : {type(results[i])} did not match expected type {otype} in {call_fn}")
        if single_output:
            results = results[0]
        return results
    return call_wrapper

#This decorator does the following:
#1) Caches the function call
#2) Stores the family closure in Peak._fc_ if it can
class family_closure:
    def __init__(self, fc):
        self.fc = fc
        self.cache = {}

    def __call__(self, family, *args, **kwargs):
        key = (family, tuple(args), tuple(kwargs.items()))
        if key in self.cache:
            return self.cache[key]
        res = self.fc(family, *args, **kwargs)
        self.cache[key] = res
        return res

# Decorator for Peak classes to enable magma compilation and SMT mapping
def assemble(family, locals, globals, assembler=Assembler):
    def decorator(peak_cls):
        if family is SMTBit.get_family():
            call = peak_cls.__call__
            input_t = call._input_t
            output_t = call._output_t
            for dec in (
                begin_rewrite(),
                ssa(),
                bool_to_bit(),
                if_to_phi(family.Bit.ite),
                end_rewrite()):
                call = dec(call)
            call._input_t = input_t
            call._output_t = output_t
            peak_cls.__call__ = call
        elif family is magma.get_family():
            #Weirdly need to inject m=mamga into globals
            _globals = {**globals, "m":magma}
            env = SymbolTable(locals, _globals)
            peak_cls = magma.circuit.sequential(peak_cls, env=env)
        return peak_cls
    return decorator



