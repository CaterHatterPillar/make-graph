import argparse
import graphviz
import re
import subprocess
import sys
import unittest

def all_assignments(database):
    assignments = {}

    # accept target-specific variables
    re_assignment = re.compile(r'.*?([^:#= ]+) :?= .*$')
    re_variable = re.compile(r'\$\(([^:#= ]+?)\)')
    for line in database:
        if not any(assign in line for assign in (' = ', ' := ')):
            continue

        match_assignee = re_assignment.match(line)
        if not match_assignee:
            continue

        assignee = match_assignee.group(1)
        assignments.setdefault(assignee, set())
        for match_variable in re.finditer(re_variable, line):
            assignments[assignee].add(match_variable.group(1))

    return assignments

def without_edges(assignments):
   # not assigned other variables
    singles = {assignee for (assignee, variables) in
               assignments.iteritems() if len(variables) == 0}
    # and not assigned to another variables
    for (_, variables) in assignments.iteritems():
        singles.difference_update(variables)

    return singles

def trim(assignments, vars_to_trim):
    for var in vars_to_trim:
        assignments.pop(var, None)
    return assignments

# Alternatively, can be acquired using make --print-data-base -f /dev/null
echo_internal = """
echo:
	@echo $(subst <,\<,$(.VARIABLES))
"""  # on my system, <D is the first variable

def internal_variables():
    variables = subprocess.check_output(['make', '--eval', echo_internal])
    return set(variables.split())

def graph_assignments(assignments, include_internal):
    qualifying_assignments = trim(assignments,
                                  set(without_edges(assignments)))
    return (qualifying_assignments if include_internal else
            trim(qualifying_assignments, internal_variables()))

def nodes(assignments):
    nodes = {assignee for (assignee, _) in assignments.iteritems()}
    for (_, variables) in assignments.iteritems():
        nodes.update(variables)
    return nodes

class TestAssignments(unittest.TestCase):
    # This particular edge wouldn't appear from --print-data-base
    # output, since GNU Make would expand the variable immediately
    def test_immediate(self):
        s = ('A := a\n'
             'B := $(A)\n')
        self.assertEqual(all_assignments(s.splitlines()),
                         {'A' : set(),
                          'B' : {'A'}})

    def test_deferred(self):
        s = ('A = a\n'
             'B = $(A)\n')
        self.assertEqual(all_assignments(s.splitlines()),
                         {'A' : set(),
                          'B' : {'A'}})

    def test_empty(self):
        self.assertEqual(all_assignments('B = $(A)\n'.splitlines()),
                         {'B' : {'A'}})

    def test_multiple(self):
        self.assertEqual(all_assignments('A = $(B)$(C) $(D)\n'.splitlines()),
                         {'A' : {'B', 'C', 'D'}})

    def test_without_edges(self):
        self.assertEqual(without_edges({'A' : set(),
                                        'B' : {'A'},
                                        'C' : set()}), {'C'})

    def test_nodes(self):
        self.assertEqual(nodes({'A' : set(),
                                'B' : {'A'},
                                'C' : set()}), {'A', 'B', 'C'})

def add_nodes(dot, nodes):
    for node in nodes:
        dot.node(node)

def add_edges(dot, assignments):
    for (assignee, variables) in assignments.iteritems():
        for variable in variables:
            dot.edge(assignee, variable)

def output_graph(assignments, graph_name, view):
    dot = graphviz.Digraph(comment = 'GNU Make Variable Directional Graph')

    add_nodes(dot, nodes(assignments))
    add_edges(dot, assignments)

    dot.render(graph_name, view = view)

def output_text(assignments):
    for (assignee, variables) in sorted(assignments.iteritems()):
        sys.stdout.write('%s = %s\n' % (assignee, ' '.join(sorted(variables))))

def make_graph(database, graph_name, as_text, include_internal, view):
    assignments = graph_assignments(all_assignments(database), include_internal)
    if as_text:
        output_text(assignments)
    else:
        output_graph(assignments, graph_name, view)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument('--database', type = argparse.FileType('r'),
                        help = ("GNU Make database filename; if no filename is"
                                " provided the database is expected on the"
                                " standard input stream"))
    parser.add_argument('--graph-name', default = 'graph', dest = 'graph_name',
                        help = ("Graph name; defaults to 'graph'"))
    parser.add_argument('--include-internal', action = 'store_true',
                        help = "Include internal and implicit variables")
    parser.add_argument('--list', dest = 'as_text', action = 'store_true',
                        help = "Output as text to the standard output stream")
    parser.add_argument('--no-view', dest = 'view', action = 'store_false',
                        help = "Don't open the assembled graph")

    args = vars(parser.parse_args())
    database = args['database'] if args['database'] else sys.stdin
    make_graph(database,args['graph_name'], args['as_text'],
               args['include_internal'], args['view'])

    if database != sys.stdin:
        database.close()
