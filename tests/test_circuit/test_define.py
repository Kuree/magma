import os
import magma as m
from magma.testing import check_files_equal
import logging


def test_simple_def():
    os.environ["MAGMA_CODEGEN_DEBUG_INFO"] = "1"
    And2 = m.DeclareCircuit('And2', "I0", m.In(m.Bit), "I1", m.In(m.Bit),
                            "O", m.Out(m.Bit))

    main = m.DefineCircuit("main", "I", m.In(m.Bits(2)), "O", m.Out(m.Bit))

    and2 = And2()

    m.wire(main.I[0], and2.I0)
    m.wire(main.I[1], and2.I1)
    m.wire(and2.O, main.O)

    m.EndCircuit()

    m.compile("build/test_simple_def", main)
    del os.environ["MAGMA_CODEGEN_DEBUG_INFO"]
    assert check_files_equal(__file__, f"build/test_simple_def.v",
                             f"gold/test_simple_def.v")


def test_unwired_ports_warnings(caplog):
    caplog.set_level(logging.WARN)
    And2 = m.DeclareCircuit('And2', "I0", m.In(m.Bit), "I1", m.In(m.Bit),
                            "O", m.Out(m.Bit))

    main = m.DefineCircuit("main", "I", m.In(m.Bits(2)), "O", m.Out(m.Bit))

    and2 = And2()

    m.wire(main.I[1], and2.I1)

    m.EndCircuit()

    m.compile("build/test_unwired_output", main)
    assert check_files_equal(__file__, f"build/test_unwired_output.v",
                             f"gold/test_unwired_output.v")
    assert caplog.records[0].msg == "main.And2_inst0.I0 not connected"
    assert caplog.records[1].msg == "main.O is unwired"


def test_2d_array_error(caplog):
    And2 = m.DeclareCircuit('And2', "I0", m.In(m.Bit), "I1", m.In(m.Bit),
                            "O", m.Out(m.Bit))

    main = m.DefineCircuit("main", "I", m.In(m.Array(2, m.Array(3, m.Bit))), "O", m.Out(m.Bit))

    and2 = And2()

    m.wire(main.I[1][0], and2.I1)

    m.EndCircuit()

    try:
        m.compile("build/test_unwired_output", main)
        assert False, "Should raise exception"
    except Exception as e:
        assert str(e) == "Argument main.I of type Array(2,Array(3,Out(Bit))) is not supported, the verilog backend only supports simple 1-d array of bits of the form Array(N, Bit)"
