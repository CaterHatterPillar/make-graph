import re
import sys

from argparse import ArgumentParser, FileType
from graphviz import Digraph

def relations(database):
    assignments = {}

    re_assignment = re.compile('^(\w+) :?= .*$')
    re_variable = re.compile('\$\((\w+)\)')
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

def make_graph(database, graph, view):
    assignments = relations(database)

    nodes = {assignee for (assignee, _) in assignments.iteritems()}
    [nodes.update(variables) for (_, variables) in assignments.iteritems()]

    dot = Digraph(comment = 'GNU Make Variable Graph')
    [dot.node(node) for node in nodes]
    [dot.edge(assignee, var) for (assignee, variables) in
     assignments.iteritems() for var in variables]

    dot.render(graph, view = view)

if __name__ == "__main__":
    parser = ArgumentParser(__file__)
    parser.add_argument('--database', type = FileType('r'),
                        help = ("GNU Make database filename; if no filename is"
                                " provided the database is expected on the"
                                " standard input stream"))
    parser.add_argument('--graph', default = 'graph',
                        help = ("Graph name; defaults to 'graph'"))
    parser.add_argument('--include-single', action = 'store_true',
                        help = "Include lone nodes")

    args = vars(parser.parse_args())
    database = args['database'] if args['database'] else sys.stdin
    make_graph(database, args['graph'], args['view'])

    if database != sys.stdin:
        database.close()
