import magma as m
import mantle
from collections import namedtuple

@m.cache_definition
def wrap_with_disassembler(PE, disassembler, width, layout, inst_type):
    WrappedIO = []
    for key, value in PE.interface.ports.items():
        WrappedIO.append(key)
        if type(value) == m.Out(inst_type):
            WrappedIO.append(m.In(m.Bits[width]))
        else:
            WrappedIO.append(m.Flip(type(value)))

    def wire_inst_fields(wrapper_inst, pe_inst, layout):
        if isinstance(wrapper_inst, m.Product):
            for key, value in layout.items():
                begin = value[0]
                end = value[1]
                wire_inst_fields(wrapper_inst[begin:end], getattr(pe_inst,
                                                                  key),
                                 value[2])
        else:
            for key, value in layout.items():
                begin = value[0]
                end = value[1]
                region = wrapper_inst[begin:end]
                field = getattr(pe_inst, key)
                if isinstance(type(field), m._BitKind):
                    region = m.bit(region)
                m.wire(region, field)

    class WrappedPE(m.Circuit):
        IO = WrappedIO
        @classmethod
        def definition(io):
            pe = PE()
            for key, value in PE.interface.ports.items():
                if type(value) == m.Out(inst_type):
                    wire_inst_fields(getattr(io, key), getattr(pe, key),
                                     layout)
                elif value.isoutput():
                    getattr(pe, key) <= getattr(io, key)
                else:
                    getattr(io, key) <= getattr(pe, key)
    return WrappedPE




ExtendedTypeFamily = namedtuple('ExtendedTypeFamily', ['Bit', 'BitVector',
                                                       'Unsigned', 'Signed',
                                                       'Product', 'Enum',
                                                       'overflow', 'BFloat16'])

#This will call a custom version of rebind where it will apply m.circuit.sequential
def compile_magma(PE, magma_adt_dict = {}):
    #upate magma family
    family = m.get_family()
    from mantle.common.operator import overflow
    BFloat16 = m.BFloat[16]
    def reinterpret_from_bv(bv):
        return BFloat16(bv)
    def reinterpret_as_bv(bv):
        return m.Bits[16](bv)
    BFloat16.reinterpret_from_bv = reinterpret_from_bv
    BFloat16.reinterpret_as_bv = reinterpret_as_bv
    m.BitVector.concat = m.concat
    family = ExtendedTypeFamily(*family, m.Product, m.Enum, overflow, BFloat16)
    return PE.rebind(family, is_magma=True, do_rebind=magma_adt_dict)
