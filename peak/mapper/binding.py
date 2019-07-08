import typing as tp
import itertools as it
from hwtypes import SMTBit, SMTBitVector, SMTSIntVector
from hwtypes import is_adt_type
from hwtypes.adt import Product, Enum


class Unbound(Enum):
    E=0
    A=1

def is_product(isa):
    return issubclass(isa,Product)

#finds all paths in the adt
#A path is a tuple of names that indicate location in nested Product
#TODO does not deal with Sum (treats it as a leaf type)
def _flatten_adt(isa,path=()) -> tp.Mapping[tuple,type]:
    if issubclass(isa,Product):
        res = {}
        for name,t in isa.field_dict.items():
            res.update(_flatten_adt(t,path+(name,)))
        return res
    else:
        return {path:isa}

def _sort_by_t(path2t : tp.Mapping[tuple,type]) ->tp.Mapping[type,tp.List[tuple]]:

    t2path = {}
    for tup,t in path2t.items():
        t2path.setdefault(t, []).append(tup)

    return t2path

#constructs a default instruction
def _default_instr(isa,forall=False):
    if issubclass(isa,Product):
        return isa(**{name:_default_instr(t,forall) for name,t in isa.field_dict.items()})
    elif issubclass(isa,Enum):
        return isa.fields[0]
    elif forall:
        return isa()
    else:
        return isa(0)

def _get_from_path(instr,path):
    if path is ():
        return instr
    else:
        assert isinstance(instr,Product)
        return _get_from_path(getattr(instr,path[0]),path[1:])

def _set_from_path(instr,path,val):
    setattr(_get_from_path(instr,path[:-1]),path[-1],val)


#Set up binding as a matching between two instructions.
#The top level 'sim' interface is itself just a "single instruction" which is a product.

class Binder:
    def __init__(self,
        arch_isa : Product,
        ir_isa : Product,
        allow_exists : bool, #allow unbound to be Existential
        enumeration_scheme : tp.Mapping[type,tp.Callable] = {}
    ):
        self.enumeration_scheme = enumeration_scheme

        #highest level interface to binder must be a Product.
        assert issubclass(arch_isa,Product)
        assert issubclass(ir_isa,Product)
        self.arch_isa = arch_isa
        self.ir_isa = ir_isa

        self.arch_flat = _flatten_adt(self.arch_isa)
        self.ir_flat = _flatten_adt(self.ir_isa)

        arch_by_t = _sort_by_t(self.arch_flat)
        ir_by_t = _sort_by_t(self.ir_flat)

        def _has_binding(arch_by_t,ir_by_t):
            #for each type, each input of the type in the IR needs to at least be able to bind to one other in the arch
            for t in ir_by_t:
                if not (t in arch_by_t):
                    return False
                if len(arch_by_t[t]) < len(ir_by_t[t]):
                    return False
            return True

        #Check if there is at least one input binding
        self.has_binding = _has_binding(arch_by_t,ir_by_t)

        #check for early out
        if not self.has_binding:
            return
        possible_matching = {}
        for arch_type, arch_paths in arch_by_t.items():
            if is_adt_type(arch_type): #Sum or Enum
                unbound_possibilities = (Unbound.E,)
            elif allow_exists:
                unbound_possibilities = (Unbound.A,Unbound.E)
            else:
                unbound_possibilities = (Unbound.A,)

            #Returns this list of things that match type t from arch
            ir_paths = ir_by_t.setdefault(arch_type, [])
            num_unbound = len(arch_paths) - len(ir_paths)

            #Create a potentials list (to be passed to product)
            #This will tie each unbound variable with either "Universal" or "Existential"
            ir_path_potentials = list(it.chain(((path,) for path in ir_paths), it.repeat(unbound_possibilities,num_unbound)))
            assert len(ir_path_potentials) == len(arch_paths)
            for ir_path in it.product(*ir_path_potentials):
                #For every permutation of arch, match it with ir
                for arch_perm in it.permutations(arch_paths):
                    possible_matching.setdefault(arch_type, []).append(list(zip(ir_path, arch_perm)))

        self.possible_matching = possible_matching

        del arch_by_t
        del ir_by_t

    #This will yield a "binding" which is a list of (ir_path,arch_path) pairs
    def enumerate(self):
        assert self.has_binding
        for l in it.product(*self.possible_matching.values()):
            yield it.chain(*l)

    def get_enumerate(self,t):
        #custom enumeration
        try:
            return self.enumeration_scheme[t]
        except:
            #default scheme
            if is_adt_type(t):
                def gen():
                    return t.enumerate()
                return gen
            elif issubclass(t,SMTBitVector):
                def gen():
                    for val in (0,-1):
                        yield t(val)
                return gen
            elif issubclass(t,SMTBit):
                def gen():
                    for val in (0,1):
                        yield t(val)
                return gen
            else:
                raise ValueError(str(t))

    #This will enumerate a particular binding and yield a concrete instruction
    def enumerate_binding(self,binding,ir_instr):
        #I want to modify and return the binding list
        binding_list = list(binding)
        assert self.has_binding
        arch_instr = _default_instr(self.arch_isa)
        E_paths = []
        E_idxs = []
        for bi,(ir_path,arch_path) in enumerate(binding_list):
            if ir_path == Unbound.E: #existentially qualified
                E_paths.append(arch_path)
                E_idxs.append(bi)
                continue
            if ir_path == Unbound.A: #universally qualified
                arch_type = self.arch_flat[arch_path]
                arch_var = arch_type()
            else:
                arch_var = _get_from_path(ir_instr,ir_path)
            _set_from_path(arch_instr,arch_path,arch_var)

        #enumerate the E_types
        E_poss = [self.get_enumerate(self.arch_flat[path])() for path in E_paths]
        for E_binding in it.product(*E_poss):
            assert len(E_paths)==len(E_binding)
            assert len(E_paths)==len(E_idxs)
            for arch_path,inst,idx in zip(E_paths,E_binding,E_idxs):
                _set_from_path(arch_instr,arch_path,inst)
                binding_list[idx] = (inst,binding_list[idx][1])
            yield arch_instr, binding_list
