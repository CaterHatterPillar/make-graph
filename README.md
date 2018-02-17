## make_graph.py

Assemble a directed graph visualizing the relationships between GNU
Make variables using Graphviz.

## Synopsis

`make --print-data-base | python make_variable_graph.py [options]`

## Limitations

* GNU Make expand immediate variables on-sight, so series of immediate assignments are not accurately represented in the graph
