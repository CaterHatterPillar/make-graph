import re
import sys

from collections import defaultdict
from graphviz import Digraph

with open('internal.vars') as internal:
    internal = internal.readlines()

assignments = defaultdict(set)

re_assignment = re.compile('^(\w+) :?= .*$')
re_variable = re.compile('\$\((\w+)\)')
for line in sys.stdin:
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

dot.render('graph', view=True)
