from ..array import ArrayKind, ArrayType
from ..bit import BitType, VCC, GND
from collections import OrderedDict

from graphviz import Digraph
import re

# Initially based on the firrtl backend.

def escape(s):
    # Escape special characters for graphviz labels.
    return re.sub(r'([<>])', r'\\\1', s)

def get_type(port):
    if isinstance(port, ArrayType):
        width = port.N
    else:
        assert isinstance(port, BitType)
        width = 1
    return "UInt<{}>".format(width)

def get_name(dot, port):
    if port is VCC: return "1"
    if port is GND: return "0"

    if isinstance(port, ArrayType):
        if not port.iswhole(port.ts):
            # the sequence of values is concantenated
            port = [get_name(dot, i) for i in port.ts]
            port.reverse()
            if len(port) == 1:  # FIXME: Hack to make single length bit arrays work
                return port[0]
            name = '[' + ','.join(port) + ']'
            dot.node(name, '{{' + '|'.join(port) + '}|}')
            for sub in port:
                dot.edge(sub, name + ':' + sub)
            return name
    assert not port.anon()
    return port.name.qualifiedname(sep="_")

def compileinstance(dot, instance):
    instance_name = str(instance.name)
    instance_cls_name = str(instance.__class__.__name__)

    inputs = []
    outputs = []

    for name, port in instance.interface.ports.items():
        if port.isinput():
            inputs.append('<{0}> {0}'.format(str(name)))
            value = port.value()
            if not value:
                print('Warning (firrtl): input', str(port), 'not connected to an output')
                value = port
        else:
            outputs.append('<{0}> {0}'.format(str(name)))
            value = port
        # if isinstance(value, ArrayType):
        #     for index, subport in enumerate(value.ts):
        #         s += "{}.{}[{}] <= {}\n".format(instance_name, name, index, get_name(subport))
        # else:
        value_name = get_name(dot, value)
        if port.isinput():
            # s += "{}.{} <= {}\n".format(instance_name, name, value_name)
            dot.edge(value_name, '{}:{}'.format(instance_name, name))
        else:
            # s += "{} <= {}.{}\n".format(value_name, instance_name, name)
            dot.edge('{}:{}'.format(instance_name, name), value_name)

    instance_label = '{' + '|'.join(inputs) + '}|' + \
                     '{}\\n{}'.format(instance_name, instance_cls_name) + \
                     '|{' + '|'.join(outputs) + '}'
    dot.node(instance_name, '{' + instance_label + '}')

def compiledefinition(dot, cls):
    # Each definition maps to an entire self-contained graphviz digraph.

    # for now only allow Bit or Array(n, Bit)
    for name, port in cls.interface.ports.items():
        if isinstance(port, ArrayKind):
            if not isinstance(port.T, BitKind):
                print('Error: Argument', port, 'must be a an Array(n,Bit)')

    for name, port in cls.interface.ports.items():
        # TODO: Check whether port.isinput() or .isoutput().
        dot.node(name,
                 escape('{}\\n{}'.format(name, get_type(port))),
                 shape='ellipse')

    # declare a wire for each instance output
    for instance in cls.instances:
        for port in instance.interface.ports.values():
            if port.isoutput():
                dot.node(get_name(dot, port),
                         escape('{}\\n{}'.format(get_name(dot, port), get_type(port))),
                         shape='none')

    # Emit the graph node (with ports) for each instance.
    for instance in cls.instances:
        compileinstance(dot, instance)

    # Assign to module output arguments.
    for input in cls.interface.inputs():
        output = input.value()
        if output:
            iname = get_name(dot, input)
            oname = get_name(dot, output)
            dot.edge(oname, iname)

def find(circuit, defn):
    name = circuit.name
    if not hasattr(circuit, "instances"):
        return defn
    for i in circuit.instances:
        find(type(i), defn)
    if name not in defn:
        defn[name] = circuit
    return defn

def to_html(main):
    defn = find(main,OrderedDict())

    dots = []
    for k, v in defn.items():
         print('compiling', k, v)
         dot = Digraph(k,
                       graph_attr={'label': k, 'rankdir': 'LR'},
                       node_attr={'shape': 'record'})
         compiledefinition(dot, v)
         dots.append(dot)

    return "\n".join([dot._repr_svg_() for dot in dots])

def compile(main):
    defn = find(main,OrderedDict())

    dots = []
    for k, v in defn.items():
         print('compiling', k, v)
         dot = Digraph(k,
                       graph_attr={'label': k, 'rankdir': 'LR'},
                       node_attr={'shape': 'record'})
         compiledefinition(dot, v)
         dots.append(dot)

    return '\n'.join([str(dot) for dot in dots]) + '\n'
