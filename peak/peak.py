from collections import OrderedDict, namedtuple
from hwtypes import TypeFamily, AbstractBitVector, AbstractBit, is_adt_type, SMTBitVector
from hwtypes.adt import Product, Sum, Enum, Tuple
from hwtypes.adt_util import rebind_bitvector
from hwtypes.modifiers import is_modified, get_modifier, get_unmodified
import functools
import inspect
import textwrap
from ast_tools.stack import get_symbol_table, SymbolTable
import magma as m

Src = namedtuple("Src",["code","filename"])

def rebind_type(T,family, dont_rebind=(), is_magma=False):
    def _rebind_bv(T):
        return rebind_bitvector(T,AbstractBitVector,family.BitVector).rebind(AbstractBit,family.Bit,True)
    if T in dont_rebind:
        return T
    elif T in (AbstractBitVector,AbstractBit,Product,Sum,Tuple,Enum,Peak):
        return T
    elif not inspect.isclass(T):
        return T
    elif is_modified(T):
        return get_modifier(T)(rebind_type(get_unmodified(T),family,dont_rebind,is_magma))
    elif issubclass(T, Peak):
        return T.rebind(family, dont_rebind, is_magma)

    elif issubclass(T,AbstractBitVector):
        return rebind_bitvector(T,AbstractBitVector,family.BitVector)
    elif issubclass(T,AbstractBit):
        return family.Bit
    elif issubclass(T,(Product,Sum)):
        return _rebind_bv(T)
    else:
        return T


RESERVED_SUNDERS = frozenset({'_env_', '_src_'})
class ReservedNameError(Exception): pass

#This will save the locals and globals in Class._env_
peak_cache = {}
class PeakMeta(type):
    def __new__(mcs,name,bases,attrs,**kwargs):
        for rname in RESERVED_SUNDERS:
            if rname in attrs:
                raise ReservedNameError(f"Attribute {rname} is reserved")
        cls = super().__new__(mcs,name,bases,attrs,**kwargs)
        env = get_symbol_table()
        cls._env_ = env
        return cls

    #This will rebind the class to a specific family
    def rebind(cls, family, dont_rebind=(), is_magma=False):
        assert hasattr(cls,"_env_")
        #try to get the soruce code if it does not have it
        if not hasattr(cls,'_src_'):
            try:
                src_lines, lineno = inspect.getsourcelines(cls)
                filename = inspect.getsourcefile(cls)
            except TypeError:
                raise TypeError(f"PEak class {cls} does not have a source file. Source code needs to be attached directly to {cls.__name_}._srccode_")
            #This magic allows for error messaging to reference the correct line number
            indented_program_txt = "".join(["\n"*(lineno-1)]+src_lines)
            program_txt = textwrap.dedent(indented_program_txt)
            cls._src_ = Src(code=program_txt, filename=filename)

        #check cache
        #print(cls, cls.uniquify())
        #rebound_cls = peak_cache.get((family,cls._src_,cls.uniquify()))
        #if rebound_cls is not None:
        #    print("FOUND")
        #    for f,src,u in peak_cache.keys():
        #        print(u)
        #    print("\FOUND")
        #    return rebound_cls

        #re-exec the source code
        #but with a new environment which replaced all references
        #to a particular BitVector with the passed in family's bitvector
        dont_rebind += (cls,)
        _locals = {k:rebind_type(t, family, dont_rebind, is_magma) for k,t in cls._env_.locals.items()}
        _globals = {k:rebind_type(t, family, dont_rebind, is_magma) for k,t in cls._env_.globals.items()}

        #for k,v in cls.__en


        env = SymbolTable(locals=_locals, globals=_globals)

        exec_ls = {}
        exec(compile(cls._src_.code,cls._src_.filename,'exec'),dict(env),exec_ls)
        rebound_cls = exec_ls[cls.__name__]
        rebound_cls._src_ = cls._src_
        if is_magma:
            rebound_cls = m.circuit.sequential(rebound_cls, env=env)

        #Add back to cache
        #peak_cache[(family, cls._src_, cls.uniquify())] = rebound_cls
        return rebound_cls

    #Returns the input interface as a product type
    def get_inputs(cls):
        assert hasattr(cls.__call__,'_peak_inputs_')
        return cls.__call__._peak_inputs_

    #returns the input interface as a product type
    def get_outputs(cls):
        assert hasattr(cls.__call__,'_peak_outputs_')
        return cls.__call__._peak_outputs_

class Peak(metaclass=PeakMeta):
    def __init__(self):
        pass

    @classmethod
    def uniquify(cls):
        return 0

def name_outputs(**output_dict):
    """Decorator meant to apply to any function to specify output types
    A Product of the output types will be stored in fn._peak_outputs_
    A Product of the input types will be stored in fn._peak_inputs_
    Will verify that all the input/outputs have type annotations
    Will also typecheck the inputs/outputs
    """
    def decorator(call_fn):
        @functools.wraps(call_fn)
        def call_wrapper(*args,**kwargs):
            results = call_fn(*args,**kwargs)
            single_output = not isinstance(results,tuple)
            if single_output:
                results = (results,)
            for i, (oname, otype) in enumerate(output_dict.items()):
                if not isinstance(results[i], otype):
                    raise TypeError(f"result type for {oname} : {type(results[i])} did not match expected type {otype}")
            if single_output:
                results = results[0]
            return results

        #Set all the outputs
        outputs = OrderedDict()
        for oname,otype in output_dict.items():
            if not issubclass(otype, (AbstractBitVector, AbstractBit, m.Bit, m.BitVector)):
                raise TypeError(f"{oname} is not a Bitvector class")
            outputs[oname] = otype
        call_wrapper._peak_outputs_ = Product.from_fields("PeakOutputs",outputs)
        #set all the inputs
        arg_offset = 1 if call_fn.__name__ == "__call__" else 0
        num_inputs = call_fn.__code__.co_argcount
        input_names = call_fn.__code__.co_varnames[arg_offset:num_inputs]
        in_types = call_fn.__annotations__
        in_type_keys = set(in_types.keys())
        # Remove return annotation if it exists
        if "return" in in_type_keys:
            in_type_keys.remove("return")
        if set(input_names) != set(in_type_keys):
            raise TypeError(f"Missing type annotations on inputs: {set(input_names)} != {set(in_type_keys)}")
        inputs = OrderedDict()
        for name in input_names:
            input_type= in_types[name]
            inputs[name] = in_types[name]
        call_wrapper._peak_inputs_ = Product.from_fields("PeakInputs",inputs)

        return call_wrapper
    return decorator

class PeakNotImplementedError(NotImplementedError):
    pass

class PeakUnreachableError(NotImplementedError):
    pass


