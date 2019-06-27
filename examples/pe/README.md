Specification of the Stanford CGRA Processing Element (PE)

- phanrahan/pe for the current spec. And pe/tests for directed tests.

- garnet/test_simple_pe.py for comparisons between the spec
and the verilog model; written in fault

- correct errors in spec

Notes
- NYI
  - independent compare
  - mult0 C=res>=1<<16
  - mult1 C=res>=1<<24
  - mult2 C=0
- differences from current spec
  - abs C=N
  - gte C=a>=b
  - lte C=a<=b
  - rshift, lshift C=shifted value, c shifted in
  - logical operations: C=a+b>=1<<16
  

- extended precision mult?
- shift
- rotate?
- sbc
- lut
  - independent output
  - 4-bit lut?

cond
- outputting 0 through lut
- outputting 1 through lut

rationale for placing the registers before the ALU

debug irq?
  debug_res
  debug_res_p
  debug_irq_en

acc?
