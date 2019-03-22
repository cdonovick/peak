import magma as m


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
