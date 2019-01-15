import functools as ft
from peak.pe1 import sim
from SMT_bit_vector import SMTBitVector, SMTSIntVector, SMTUIntVector, ss

solver = ss.smt('Z3')

bound_BV = ft.partial(SMTBitVector, solver)
bound_SInt = ft.partial(SMTSIntVector, solver)
bound_UInt = ft.partial(SMTUIntVector, solver)

alu = sim.gen_alu(bound_BV, bound_SInt, bound_UInt)
a = bound_BV(None, sim.DATAWIDTH, name='a')
b = bound_BV(None, sim.DATAWIDTH, name='b')

alu_res, alu_res_p, Z, N, C, V = alu(sim.ALU.And, 0, a, b, 0)

mapping_constraint = alu_res.value != a.value & b.value
print(mapping_constraint)
solver.Assert(mapping_constraint)
assert not solver.CheckSat()
