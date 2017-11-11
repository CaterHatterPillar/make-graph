import argparse
import graphviz
import re
import subprocess
import sys

def relations(database):
    assignments = {}

    re_assignment = re.compile(r'^([^:#= ]+) :?= .*$')
    re_variable = re.compile(r'\$\(([^:#= ]+)\)')
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

def trim_singles(assignments):
    for variable in set(without_edges(assignments)):
        assignments.pop(variable, None)
    return assignments

def nodes(assignments):
    nodes = {assignee for (assignee, _) in assignments.iteritems()}
    for (_, variables) in assignments.iteritems():
        nodes.update(variables)
    return nodes

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

def make_graph(database, graph_name, as_text, view):
    assignments = trim_singles(relations(database))
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
    parser.add_argument('--list', dest = 'as_text', action = 'store_true',
                        help = "Output as text to the standard output stream")
    parser.add_argument('--no-view', dest = 'view', action = 'store_false',
                        help = "Don't open the assembled graph")

    args = vars(parser.parse_args())
    database = args['database'] if args['database'] else sys.stdin
    make_graph(database, args['graph_name'], args['as_text'], args['view'])

    if database != sys.stdin:
        database.close()
