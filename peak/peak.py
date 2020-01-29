from collections import OrderedDict
from hwtypes import TypeFamily, AbstractBitVector, AbstractBit, BitVector, Bit, is_adt_type
from hwtypes.adt import Product, Tuple
import functools
from inspect import isclass
from ast_tools.passes import begin_rewrite, end_rewrite
from ast_tools.passes import ssa, bool_to_bit, if_to_phi
from ast_tools.stack import SymbolTable
from hwtypes import make_modifier
from hwtypes import SMTBit
from hwtypes.adt import Enum
from hwtypes.adt_meta import EnumMeta, AttrSyntax, GetitemSyntax
from peak.assembler import Assembler
from peak.assembler.utils import assemble_values_in_func
import inspect
import magma
import warnings


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
        call_fn.output_t = output_t
        return call_fn
    return decorator

#Will color warnings yellow
def warn(msg):
    return warnings.warn(f"\033[1;33m{msg}\nPeak compiler will not work correctly.\033[1;0m")

def set_input_output(call_fn):
    try:
        output_t = call_fn.output_t
    except:
        try:
            output_types = call_fn.__annotations__['return']
        except KeyError:
            warn(f"Missing output type annotations on __call__ {call_fn}")
            return call_fn
        except AttributeError:
            warn(f"Missing definition for __call__ {call_fn}")
            return call_fn
        if output_types is None:
            output_t = None
        else:
            if not isinstance(output_types, tuple):
                output_types = (output_types,)
            output_t = Tuple[output_types]

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
        warn(f"Missing type annotations on inputs: {set(input_names)} != {set(in_type_keys)}")
        return call_fn

    for name in input_names:
        input_type= in_types[name]
        peak_inputs[name] = in_types[name]
    input_t = Product.from_fields("Input", peak_inputs)

    @functools.wraps(call_fn)
    def call_wrapper(*args, **kwargs):
        results = call_fn(*args, **kwargs)
        single_output = not isinstance(results, tuple)
        if single_output:
            results = (results,)
        for i, (oname, otype) in enumerate(output_t.field_dict.items()):
            if not isinstance(results[i], otype):
                warn(f"result type for output {oname} : {type(results[i])} did not match expected type {otype} in {call_fn}")
        if single_output:
            results = results[0]
        return results

    call_wrapper.input_t = input_t
    call_wrapper.output_t = output_t
    return call_wrapper

class PeakMeta(type):
    @property
    def input_t(cls):
        #peak classes should always have input_t
        assert hasattr(cls.__call__, 'input_t')
        return cls.__call__.input_t

    @property
    def output_t(cls):
        #peak classes should always have output_t
        assert hasattr(cls.__call__, 'output_t')
        return cls.__call__.output_t

    def __new__(mcs, name, bases, attrs, unsafe=False, **kwargs):
        cls = super().__new__(mcs, name, bases, attrs, **kwargs)
        if "__call__" in attrs and (not unsafe):
            cls.__call__ = set_input_output(cls.__call__)
            assert cls.__call__ is not None
        return cls

class Peak(metaclass=PeakMeta): pass

class PeakNotImplementedError(NotImplementedError):
    pass



#Helper function to search for the one peak class
def get_Peak_cls(fc_out):
    clss = []
    if not isinstance(fc_out, tuple):
        fc_out = (fc_out,)
    for cls in fc_out:
        if inspect.isclass(cls) and issubclass(cls, Peak):
            clss.append(cls)
    if len(clss) == 1:
        return clss[0]
    raise TypeError(f"Need to return one Peak class instead of {len(clss)} Peak classes: {fc_out}")


#This decorator does the following:
#1) Caches the function call
#2) Stores the family closure in Peak._fc_
class family_closure:
    def __init__(self, fc):
        self.fc = fc

        num_inputs = fc.__code__.co_argcount
        if num_inputs != 1:
            warn("Family Closure should take a single input 'family'")
        functools.update_wrapper(self, fc)
        self.cache = {}

    def __call__(self, family):
        if family in self.cache:
            return self.cache[family]
        cls = self.fc(family)
        try:
            peak_cls = get_Peak_cls(cls)
            peak_cls._fc_ = self
        except TypeError as e:
            if family is not magma.get_family():
                warn(f"Family closure should return one Peak class, Instead {e}")
        self.cache[family] = cls
        return cls

class PeakNotImplementedError(NotImplementedError):
    pass

# Decorator for Peak classes to enable magma compilation and SMT mapping
def assemble(family, locals, globals, assembler=Assembler):
    def decorator(peak_cls):
        if family is SMTBit.get_family():
            call = peak_cls.__call__
            input_t = call.input_t
            output_t = call.output_t
            for dec in (
                begin_rewrite(),
                ssa(),
                bool_to_bit(),
                if_to_phi(family.Bit.ite),
                end_rewrite()):
                call = dec(call)
            call.input_t = input_t
            call.output_t = output_t
            peak_cls.__call__ = call
        elif family is magma.get_family():
            #Weirdly need to inject m=mamga into globals
            _globals = {**globals,"m":magma}
            env = SymbolTable(locals,_globals)
            peak_cls = magma.circuit.sequential(peak_cls, env=env)
        return peak_cls
    return decorator


Const = make_modifier("Const")

def Enum_fc(family):
    if family is magma.get_family():
        return magma.Enum
    else:
        return Enum

def Product_fc(family):
    if family is magma.get_family():
        return magmaa.Product
    else:
        return Product

def Tuple_fc(family):
    if family is magma.get_family():
        return magma.Tuple
    else:
        return Tuple


