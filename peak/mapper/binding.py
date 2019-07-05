import typing as tp
import itertools as it
from hwtypes import SMTBit, SMTBitVector, SMTSIntVector

def _group_by_value(d : tp.Mapping[tp.Any, type]) -> tp.Mapping[type, tp.List[tp.Any]]:
    nd = {}
    for k,v in d.items():
        nd.setdefault(v, []).append(k)

    return nd


#Set up binding as a matching between two instructions.
#The top level interface is itself just a "single instruction" which is a product.


#This will deal with bindings
class Binder:
    def __init__(self,
        arch_inputs : tp.Mapping[str,type],
        arch_outputs : tp.Mapping[str,type],
        ir_inputs : tp.Mapping[str,type],
        ir_outputs : tp.Mapping[str,type],
    ):
        self.arch_inputs = arch_inputs
        self.arch_outputs = arch_outputs
        self.ir_inputs = ir_inputs
        self.ir_outputs = ir_outputs

        #type : List[names]
        arch_inputs_by_t = _group_by_value(arch_inputs)
        ir_inputs_by_t = _group_by_value(ir_inputs)

        #Idea: do bindings of instructions as well. This means extract out all the 
        #This requires fancy parsing of the instrcution. instructions can be enumerated (via forloop) or be used in SMT (make this generic)

        def _has_binding(arch_by_t,ir_by_t):
            #for each type, each input of the type in the IR needs to at least be able to bind to one other in the arch
            for t in ir_by_t:
                if not (t in arch_by_t):
                    return False
                if len(arch_by_t[t]) < len(ir_by_t[t]):
                    return False
            return True

        #Check if there is at least one input binding
        self.has_binding = _has_binding(arch_inputs_by_t,ir_inputs_by_t)
        #And at least one output binding
        self.has_binding &= _has_binding(
            _group_by_value(arch_outputs),
            _group_by_value(ir_outputs)
        )
        #check for early out
        if not self.has_binding:
            return
        possible_matching = {}
        missing_inputs_by_t = {}
        for arch_type, arch_input_names in arch_inputs_by_t.items():
            #Returns this list of things that match type t from arch
            ir_input_names = ir_inputs_by_t.setdefault(arch_type, [])
            type_diff = len(arch_input_names) - len(ir_input_names)
            missing_inputs_by_t[arch_type] = type_diff
            #expand the list to be the same size as arch (with Nones)
            ir_input_names = list(it.chain(ir_input_names, it.repeat(None, type_diff)))
            assert len(ir_input_names) == len(arch_input_names)
            #For every permutation of arch_input_names, match it with ir_input_names
            for arch_perm in it.permutations(arch_input_names):
                possible_matching.setdefault(arch_type, []).append(list(zip(ir_input_names, arch_perm)))

        self.possible_matching = possible_matching
        self.missing_inputs_by_t = missing_inputs_by_t

        del arch_inputs_by_t
        del ir_inputs_by_t

    #Returns a list of all possible bindings
    #TODO should be a generator
    def get_bindings(self):
        assert self.has_binding
        bindings = []
        for l in it.product(*self.possible_matching.values()):
            bindings.append(list(it.chain(*l)))
        return bindings

    #Will enumerate all possible missing input bindings
    #TODO add in Constant values (0,-1) instead of just SMTVar
    #TODO should be a generator
    def get_missing_inputs_list(self) -> tp.List[tp.Mapping[type,SMTBitVector]]:
        assert self.has_binding
        possible = {}
        for t,cnt in self.missing_inputs_by_t.items():
            possible[t] = [t() for _ in range(cnt)]
        return [possible]

    def construct_binding_dict(self,missing_inputs,binding,ir_smt_vars):
        assert self.has_binding
        tidx = {t:0 for t in missing_inputs}
        binding_dict = {}
        name_binding = {k : v if v is not None else "any" for v,k in binding}
        for ir_name,arch_name in binding:
            if ir_name is not None:
                binding_dict[arch_name] = ir_smt_vars[ir_name]
            else:
                arch_type = self.arch_inputs[arch_name]
                binding_dict[arch_name] = missing_inputs[arch_type][tidx[arch_type]]
                tidx[arch_type] += 1
        return binding_dict,name_binding

