import magma as m


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
        # import pdb; pdb.set_trace()
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
                # import pdb; pdb.set_trace()
                if begin != end:
                    region = wrapper_inst[begin:end]
                    field = getattr(pe_inst, key)
                    if issubclass(type(field), m.Digital):
                        region = m.bit(region)
                    if isinstance(field, m.Tuple):
                        begin_idx = 0
                        end_idx = 0
                        for idx in range(len(field)):

                            if isinstance(field[idx], m.Bit):
                                m.wire(region[begin_idx], field[idx])
                                begin_idx += 1
                            else:
                                end_idx += len(field[idx])
                                m.wire(region[begin_idx : end_idx], field[idx])
                                begin_idx += len(field[idx])
                    else:
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
                elif value.is_output():
                    getattr(pe, key) <= getattr(io, key)
                else:
                    getattr(io, key) <= getattr(pe, key)
    return WrappedPE
