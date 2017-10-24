import re
import sys

from argparse import ArgumentParser, FileType
from collections import defaultdict
from graphviz import Digraph

def relations(database, blacklist):
    assignments = defaultdict(set)

    re_assignment = re.compile('^(\w+) :?= .*$')
    re_variable = re.compile('\$\((\w+)\)')
    for line in database:
        if not any(assign in line for assign in (' = ', ' := ')):
            continue

        match_assignee = re_assignment.match(line)
        if not match_assignee:
            continue

        assignee = match_assignee.group(1)
        if assignee in blacklist:
            continue

        for match_variable in re.finditer(re_variable, line):
            variable = match_variable.group(1)
            if variable not in blacklist:
                assignments[assignee].add(variable)

    return assignments

def make_graph(database, graph, view):
    with open('internal.vars') as internal:
        internal = internal.readlines()

    assignments = relations(database, internal)

    nodes = {assignee for (assignee, _) in assignments.iteritems()}
    [nodes.update(variables) for (_, variables) in assignments.iteritems()]

    dot = Digraph(comment = 'GNU Make Variable Graph')
    [dot.node(node) for node in nodes]
    [dot.edge(assignee, var) for var in variables
     for (assignee, variables) in assignments.iteritems()]

    dot.render(graph, view = view)

if __name__ == "__main__":
    parser = ArgumentParser('make_graph.py')
    parser.add_argument('--database', type = FileType('r'),
                        help = ("GNU Make database filename; if no filename is"
                                " provided the database is expected on the"
                                " standard input stream"))
    parser.add_argument('--graph', default = 'graph',
                        help = ("Graph name; defaults to 'graph'"))
    parser.add_argument('--no-view', dest = 'view', action = 'store_false',
                        help = "Don't open the assembled graph")

    args = vars(parser.parse_args())

    database = args['database'] if args['database'] else sys.stdin
    make_graph(database, args['graph'], args['view'])

    if database != sys.stdin:
        database.close()
