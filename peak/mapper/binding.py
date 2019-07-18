import typing as tp
import itertools as it
from hwtypes import SMTBit, SMTBitVector, SMTSIntVector, AbstractBitVector, AbstractBit
from hwtypes import is_adt_type
from hwtypes.adt import Product, Enum, Sum
from .util import SubTypeDict


__ALL__ = ['Binder', 'get_from_path', 'set_from_path', 'binding_pretty_print']

def copy_smt_value(val):
    if isinstance(val,(SMTBit,SMTBitVector)):
        return type(val)(val.value)
    else:
        return val

def binding_pretty_print(binding,ts="  "):
    for p0,p1 in binding:
        if isinstance(p0,tuple):
            p0_str = ".".join(p0)
        elif isinstance(p0,Enum):
            p0_str = str(p0)
        else:
            p0_str = str(p0.value)
        p1_str = ".".join(p1)
        print(f"{ts}{p0_str} -> {p1_str}")

class Unbound(Enum):
    Existential=0
    Universal=1

def _has_binding(arch_by_t, ir_by_t):
#for each type, each input of the type in the IR needs to at least be able to bind to one other in the arch
    for t in ir_by_t:
        if not (t in arch_by_t):
            return False
        if len(arch_by_t[t]) < len(ir_by_t[t]):
            return False
    return True

#Returns a default value of a non-Product/Sum type
def default_val(isa,forall=False):
    if issubclass(isa, Enum):
        return isa.fields[0]
    elif forall:
        return isa()
    elif issubclass(isa,AbstractBitVector):
        return isa(0)
    elif issubclass(isa,AbstractBit):
        return isa(False)
    else:
        raise ValueError(str(isa))


#returns a flat map and a default instr
def _enumerate_forms(isa,path=()):
    if issubclass(isa,Product):
        sub_forms = []
        for field,t in isa.field_dict.items():
            sub_forms.append(_enumerate_forms(t,path+(field,)))
        forms = []
        fields = isa.field_dict.keys()
        for plist in it.product(*sub_forms):
            flat_update = {}
            pinstr_fields = {}
            for field, (flat, instr) in zip(fields,plist):
                flat_update.update(flat)
                pinstr_fields[field] = instr
            new_instr = isa(**pinstr_fields)
            forms.append((flat_update,new_instr))
        return forms
    elif issubclass(isa,Sum):
        sums = []
        for field,t in isa.field_dict.items():
            forms = _enumerate_forms(t,path+(field,))
            #need to update the instructions
            sums += [(flat,isa(instr)) for flat,instr in forms]
        return sums
    else:
        return [({path:isa},default_val(isa))]

def _sort_by_t(path2t : tp.Mapping[tuple, type]) ->tp.Mapping[type, tp.List[tuple]]:

    t2path = {}
    for tup, t in path2t.items():
        t2path.setdefault(t, []).append(tup)

    return t2path

#Given an adt object and a tree path to a node in that adt, returns the node
def get_from_path(instr, path):
    if path is ():
        return instr
    elif isinstance(instr,(Product,Sum)):
        return get_from_path(getattr(instr, path[0]), path[1:])
    else:
        raise RuntimeError()

#Given an adt object and a tree path to a node in that adt, sets that node
def set_from_path(instr, path, val):
    instr = get_from_path(instr, path[:-1])
    assert type(getattr(instr, path[-1])) == type(val)
    setattr(instr, path[-1], val)

def _default_adt_scheme(t):
    for k in t.enumerate():
        yield k

def _default_bv_scheme(t):
    for val in (0,-1):
        yield t(val)

def _default_bit_scheme(t):
    for val in (0, 1):
        yield t(val)

#Set up binding as a matching between two instructions.
#The top level 'sim' interface is itself just a "single instruction" which is a product.

class Binder:
    def __init__(self,
        arch_isa : Product,
        ir_isa : Product,
        allow_existential : bool, #allow unbound to be Existential
        custom_enumeration : tp.Mapping[type, tp.Callable] = ()
    ):
        self.allow_existential = allow_existential
        self.enumeration_scheme = SubTypeDict(custom_enumeration)
        for t in (Sum, Enum):
            self.enumeration_scheme.setdefault(t, _default_adt_scheme)
        self.enumeration_scheme.setdefault(SMTBitVector, _default_bv_scheme)
        self.enumeration_scheme.setdefault(SMTBit, _default_bit_scheme)

        #highest level interface to binder must be a Product.
        assert issubclass(arch_isa, Product)
        assert issubclass(ir_isa, Product)
        self.arch_isa = arch_isa
        self.ir_isa = ir_isa

    #enumerates all possible sum type combinations
    #returns (arch_flat,default_arch),(ir_flat,default_ir)
    def enumerate_forms(self):
        yield from it.product(_enumerate_forms(self.arch_isa),_enumerate_forms(self.ir_isa))

    #yields (arch_instr, Binding)
    #The Binding still can contain Unbound.Existential
    #Use enumerate_binding() to enumerate out the Unbound.Existentials
    def enumerate(self):
        for (arch_flat,arch_instr),(ir_flat,ir_instr) in self.enumerate_forms():
            arch_by_t = _sort_by_t(arch_flat)
            ir_by_t = _sort_by_t(ir_flat)

            #early out (skip) if no binding
            if not _has_binding(arch_by_t,ir_by_t):
                continue

            #This assumes you will call enumerate_binding after every yield
            self.arch_instr = arch_instr
            self.arch_flat = arch_flat
            self.ir_flat = ir_flat
            #Turn ir_instr into a forall
            for path,t in ir_flat.items():
                set_from_path(ir_instr, path, default_val(t,forall=True))
            self.ir_instr = ir_instr

            possible_matching = {}
            for arch_type, arch_paths in arch_by_t.items():
                ir_paths = ir_by_t.setdefault(arch_type, [])

                #ir_poss represents all the possible inputs that could be bound to each arch_input
                ir_poss = tuple(ir_paths)
                if issubclass(arch_type,Enum):
                    ir_poss += (Unbound.Existential,)
                elif self.allow_existential:
                    ir_poss += (Unbound.Universal, Unbound.Existential)
                else:
                    ir_poss += (Unbound.Universal,)

                #Now ir_poss has all the possible mappings for each arch_path

                #Filter out some bindings
                #Only count bindings where each ir is represented exactly once
                #Might want to decrease this restriction to find things like (0 -> x^x)
                #TODO could have this customizable 
                def filt(poss):
                    ret = True
                    for ir_path in ir_paths:
                        num_ir = poss.count(ir_path)
                        ret = ret and (num_ir==1)
                        #early out
                        if ret is False:
                            return False
                    return ret
                type_bindings = []
                for ir_match in filter(filt,it.product(*[ir_poss for _ in range(len(arch_paths))])):

                    type_bindings.append(list(zip(ir_match,arch_paths)))
                possible_matching[arch_type] = type_bindings

                #for poss in filter(filt,product(
                ##Create a potentials list (to be passed to product)
                ##This will tie each unbound variable with either "Universal" or "Existential"
                #ir_path_potentials = list(it.chain(((path,) for path in ir_paths), it.repeat(unbound_possibilities, num_unbound)))
                #assert len(ir_path_potentials) == len(arch_paths)
                #for ir_path in it.product(*ir_path_potentials):
                #    #For every permutation of arch, match it with ir
                #    for arch_perm in it.permutations(arch_paths):
                #        possible_matching.setdefault(arch_type, []).append(list(zip(ir_path, arch_perm)))

            del arch_by_t
            del ir_by_t
        #This will yield a "binding" which is a list of (ir_path, arch_path) pairs
        #the ir_path can be "unbound" being specified by either Existential or Universal
            for l in it.product(*possible_matching.values()):
                yield it.chain(*l)

    #This will enumerate a particular binding (since it contains Existentials)
    #and yield a concrete instruction along with a concrete binding
    def enumerate_binding(self, binding):
        def _get_enumeration(t):
            return self.enumeration_scheme[t](t)
        arch_instr = self.arch_instr
        #I want to modify and return the binding list
        binding_list = list(binding)
        E_paths = []
        E_idxs = []
        for bi,(ir_path, arch_path) in enumerate(binding_list):
            if ir_path is Unbound.Existential: #existentially qualified
                E_paths.append(arch_path)
                E_idxs.append(bi)
                continue
            if ir_path == Unbound.Universal: #universally qualified
                arch_type = self.arch_flat[arch_path]
                arch_var = arch_type()
            else:
                arch_var = get_from_path(self.ir_instr, ir_path)
            set_from_path(arch_instr, arch_path, arch_var)

        #enumerate the E_types
        E_poss = [_get_enumeration(self.arch_flat[path]) for path in E_paths]
        for E_binding in it.product(*E_poss):
            assert len(E_paths)==len(E_binding)
            assert len(E_paths)==len(E_idxs)
            for arch_path, inst, idx in zip(E_paths, E_binding, E_idxs):
                set_from_path(arch_instr, arch_path, inst)
                binding_list[idx] = (inst, binding_list[idx][1])

            #Need to copy since this contains SMT objects.
            #Potentially could store binding value as a string or BitVector
            binding_copy = [(path,copy_smt_value(val)) for path,val in binding_list]
            yield arch_instr, binding_copy
