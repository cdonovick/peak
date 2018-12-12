# peak
Peak : Processor Specification Language ala Newell and Bell's ISP

Implement my only Sum and Product types.
- Allow specific bit-field encodings
- Match language

Encode Pico
- generate assembly
- generate disassembler
- generate simulator

Encode PE

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
