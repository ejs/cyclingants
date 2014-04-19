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
            edge = max((n for n in graph[node] if n.next_id not in visited), key=lambda e:e.pheromones)
        except ValueError: # if there are no good choices stop looking
            break
        node = edge.next_id
        distance += edge.cost
