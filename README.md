# peak
Peak : Processor Specification Language ala Newell and Bell's ISP

Implement instructions formats using Sum and Product types.
+ Unique interpretation of each instruction. This enforces
the constraint that there is only one interpretation for
every instruction.
+ Can check that all instructions are matched

Encode Pico
- generate assembly
- generate disassembler
- generate simulator

Encode PE

Encode patt's 16-bit process

Encode Risc5

# python-switch
with switch(val) as s:
    s.case('a', process_a)
    s.case('b', lambda: process_with_data(val, num, 'other values still'))
    s.default(process_any)

# match.py
def match(value, pattern):
    for klass, func in pattern.items():
       if type(value) == klass:
            func(value)
