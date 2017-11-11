import re
import subprocess
import sys

from argparse import ArgumentParser, FileType
from graphviz import Digraph

def relations(database):
    assignments = {}

    re_assignment = re.compile('^([^:\#= ]+) :?= .*$')
    re_variable = re.compile('\$\(([^:\#= ]+)\)')
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

def exclude_no_edges(assignments):
    for var in set(without_edges(assignments)):
        assignments.pop(var, None)
    return assignments

def nodes(assignments):
    nodes = {assignee for (assignee, _) in assignments.iteritems()}
    for (_, variables) in assignments.iteritems():
        nodes.update(variables)
    return nodes

def render(assignments, name, view):
    dot = Digraph(comment = 'GNU Make Variable Graph')

    for node in nodes(assignments):
        dot.node(node)

    vars = [v for (_, variables) in assignments.iteritems() for v in variables]
    for var in vars:
        dot.edge(assignee, var)

    dot.render(name, view = view)

def output(assignments):
    for (assignee, variables) in sorted(assignments.iteritems()):
        sys.stdout.write('%s = %s\n' % (assignee, ' '.join(sorted(variables))))

def make_graph(database, graph, list, view):
    assignments = exclude_no_edges(relations(database))

    if list:
        output(assignments)
    else:
        render(assignments, graph, view)

if __name__ == "__main__":
    parser = ArgumentParser(__file__)
    parser.add_argument('--database', type = FileType('r'),
                        help = ("GNU Make database filename; if no filename is"
                                " provided the database is expected on the"
                                " standard input stream"))
    parser.add_argument('--graph', default = 'graph',
                        help = ("Graph name; defaults to 'graph'"))
    parser.add_argument('--list', action = 'store_true')
    parser.add_argument('--no-view', dest = 'view', action = 'store_false',
                        help = "Don't open the assembled graph")

    args = vars(parser.parse_args())
    database = args['database'] if args['database'] else sys.stdin
    make_graph(database, args['graph'], args['list'], args['view'])

    if database != sys.stdin:
        database.close()
