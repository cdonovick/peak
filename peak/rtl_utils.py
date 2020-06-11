import magma as m
from collections import OrderedDict

@m.cache_definition
def wrap_with_disassembler(PE, disassembler, width, layout, inst_type, wrapped_name="WrappedPE"):
    WrappedIO = OrderedDict()
    for key, value in PE.interface.ports.items():
        if isinstance(value, m.Out(inst_type)):
            vtype = m.In(m.Bits[width])
        else:
            vtype = m.Flip(type(value))
        WrappedIO[key] = vtype

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
                if issubclass(type(field), m.Digital):
                    region = m.bit(region)
                m.wire(region, field)

    class WrappedPE(m.Circuit):
        name = wrapped_name
        io = m.IO(**WrappedIO)
        pe = PE()
        for key, value in PE.interface.ports.items():
            if type(value) == m.Out(inst_type):
                wire_inst_fields(getattr(io, key), getattr(pe, key),
                                 layout)
            elif value.is_output():
                m.wire(getattr(pe, key), getattr(io, key))
            else:
                m.wire(getattr(io, key), getattr(pe, key))
    return WrappedPE
