from collections import Counter

from aco import ACOEdge


def most_marked_route(graph, start, max_distance):
    visited = set()
    distance = 0
    node = start
    while distance < max_distance:
        yield node
        visited.add(node)
        try:
            options = [(n, e) for n, e in graph.get_edges(node) if n not in visited]
            edge = max(options, key=lambda e:e[1].pheromones)
        except ValueError: # if there are no good choices stop looking
            break
        node = edge[0]
        distance += edge[1].cost
