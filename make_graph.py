import re
import sys

from argparse import ArgumentParser, FileType
from collections import defaultdict
from graphviz import Digraph

def make_graph(database, graph, view):
    with open('internal.vars') as internal:
        internal = internal.readlines()

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
        if assignee in internal:
            continue

        for match_variable in re.finditer(re_variable, line):
            assignments[assignee].add(match_variable.group(1))

    dot = Digraph(comment = 'GNU Make Variable Graph')
    dot.graph_attr['ratio'] = '0.15'
    for (assignee, variables) in assignments.iteritems():
        if assignee in internal:
            continue

        dot.node(assignee)
        [dot.node(var) for var in variables if var not in internal]
        [dot.edge(assignee, var) for var in variables if var not in internal]

    dot.render(graph, view = view)

if __name__ == "__main__":
    parser = ArgumentParser("make_graph.py")
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
