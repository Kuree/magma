import kratos
import magma as m
import os


__all__ = ["FromKratos"]


def FromKratos(kratos_inst: kratos.Generator, **kargs):
    circ_name = kratos_inst.name
    internal_gen = kratos_inst.internal_generator
    ports = internal_gen.get_port_names()
    io = []
    for port_name in ports:
        io.append(port_name)
        port = kratos_inst.ports[port_name]
        width = port.width
        size = port.size
        dir_ = m.In if port.port_direction() == \
            kratos.PortDirection.In.value else m.Out
        type_ = port.port_type()
        signed = port.signed
        if type_ == kratos.PortType.Clock.value:
            type_value = m.Clock
        elif type_ == kratos.PortType.AsyncReset.value:
            if port.active_high or port.active_high is None:
                type_value = m.AsyncReset
            else:
                type_value = m.AsyncResetN
        else:
            # normal logic/wire, loop through the ndarray to construct
            # magma arrays, notice it's in reversed order
            type_value = m.Bits[width] if not signed else m.SInt[width]
            for idx, array_width in enumerate(reversed(size)):
                type_value = m.Array[array_width, type_value]
        io.append(dir_(type_value))

    defn = m.DefineCircuit(circ_name, *io, kratos=kratos_inst)
    os.makedirs(".magma", exist_ok=True)
    filename = f".magma/{circ_name}-kratos.sv"
    # multiple definition inside the kratos instance is taken care of by
    # the track definition flag
    kratos.verilog(kratos_inst, filename=filename,
                   track_generated_definition=True,
                   **kargs)
    with open(filename, 'r') as f:
        defn.verilogFile = f.read()
    m.EndCircuit()
    return defn
