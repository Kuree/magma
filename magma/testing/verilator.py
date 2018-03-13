from .function import testvectors
import magma.config as config
import inspect
import os
import subprocess

__all__ = ['harness', 'compile']

def harness(circuit,tests):

    assert len(circuit.interface.ports.keys()) == len(tests[0])

    source = '''\
#include "V{name}.h"
#include "verilated.h"
#include <cassert>
#include <iostream>
#include <printf.h>

int main(int argc, char **argv, char **env) {{
    Verilated::commandArgs(argc, argv);
    V{name}* top = new V{name};
'''.format(name=circuit.__name__)

    source += '''
    unsigned int tests[{}][{}] = {{
'''.format(len(tests), len(tests[0]))

    for test in tests:
        testvector = ', '.join([t.as_binary_string() for t in test])
        #testvector += ', {}'.format(int(func(*test[:nargs])))
        source += '''\
        {{ {} }}, 
'''.format(testvector)
    source += '''\
    };
'''

    source += '''
    for(int i = 0; i < {}; i++) {{
        unsigned int* test = tests[i];
        std::cout << "===== Test Iteration " << i << " =====" << std::endl;
        std::cout << "Inputs: " << std::endl;
'''.format(len(tests))

    i = 0
    for name, port in circuit.interface.ports.items():
        if port.isoutput():
            source += '''\
        top->{name} = test[{i}];
        printf("{name} = 0x%x ", test[{i}]);
'''.format(name=name,i=i)
        i += 1

    source += '''\
        std::cout << std::endl;
        top->eval();
'''

    i = 0
    for name, port in circuit.interface.ports.items():
        if port.isinput():
            source += '''\
        printf("Expected {name} = 0x%x\\n", test[{i}]);
        // For some reason top->port doesn't show up in cout, printf works though
        printf("Actual {name}   = 0x%x\\n", top->{name});
        assert(top->{name} == test[{i}]);
'''.format(name=name,i=i)
        i += 1
    source += '''\
    }
'''

    source += '''
    delete top;
    std::cout << "Success" << std::endl;
    exit(0);
}'''

    return source

def compile(basename, circuit, tests, input_ranges=None):
    if config.get_compile_dir() == 'callee_file_dir':
        (_, filename, _, _, _, _) = inspect.getouterframes(inspect.currentframe())[1]
        file_path = os.path.dirname(filename)
        filename = os.path.join(file_path, basename)
    else:
        filename = basename

    if callable(tests):
        tests = testvectors(circuit, tests, input_ranges)
    verilatorcpp = harness(circuit, tests)

    with open(filename, "w") as f:
        f.write(verilatorcpp)

def run_verilator_test(verilog_file_name, driver_name, top_module, verilator_flags="", build_dir=None):
    if isinstance(verilator_flags, list):
        if not all(isinstance(flag, str) for flag in verilator_flags):
            raise ValueError("verilator_flags should be a str or list of strs")
        verilator_flags = " ".join(verilator_flags)
    if build_dir is None:
        if config.get_compile_dir() == 'callee_file_dir':
            (_, filename, _, _, _, _) = inspect.getouterframes(inspect.currentframe())[1]
            file_path = os.path.dirname(filename)
            build_dir = os.path.join(file_path, 'build')
        else:
            build_dir = "build"
    assert not subprocess.call('verilator -Wall -Wno-INCABSPATH -Wno-DECLFILENAME {} --cc {}.v --exe {}.cpp --top-module {}'.format(verilator_flags, verilog_file_name, driver_name, top_module), cwd=build_dir, shell=True)
    assert not subprocess.call('make -C obj_dir -j -f V{0}.mk V{0}'.format(top_module), cwd=build_dir, shell=True)
    assert not subprocess.call('./obj_dir/V{}'.format(top_module), cwd=build_dir, shell=True)
