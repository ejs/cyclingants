from collections import Counter

from sizing import total_size


def find_most_connected_node(graph):
    most_connected, starting_points = 0, []
    for node, edges in graph.items():
        if len(edges) > most_connected:
            most_connected = len(edges)
            starting_points = [node]
        elif len(edges) == most_connected:
            starting_points.append(node)
    return starting_points


def most_marked_route(graph, start):
    visited = set()
    node = start
    while True:
        yield node
        visited.add(node)
        try:
            node = max((n for n in graph[node] if n.next_id not in visited), key=lambda e:e.pheromones).next_id
            if node in visited:
                break
        except:
            break
