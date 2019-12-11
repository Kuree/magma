import kratos
from magma.from_kratos import FromKratos


def test_kratos_types():
    mod = kratos.Generator("mod")
    in_ = mod.input("in", 8, size=[2, 4])
    out = mod.output("out", 8, size=[2, 4])
    clk = mod.clock("clk")
    rst = mod.reset("rst")
    mod.wire(out, in_)
    circuit_cls = FromKratos(mod)
    io_def = dict(circuit_cls.IO.items())
    assert str(io_def["in"]) == "Array[2, Array[4, In(Bits[8])]]"
    assert str(io_def["out"]) == "Array[2, Array[4, Out(Bits[8])]]"
    assert str(io_def["clk"] == "Clock")
    assert str(io_def["rst"]) == "In(AsyncReset)"
