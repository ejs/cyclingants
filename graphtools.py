from collections import Counter

from aco import ACOEdge


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


def clean_graph(graph):
    stats = Counter(len(b) for b in graph.values())
    while stats[0] or stats[1] or stats[2]:
        for nid in list(graph.keys()):
            if len(graph[nid]) == 0: # remove anything that has been emptied
                del graph[nid]
            elif len(graph[nid]) == 1: # remove dead ends
                nextid = graph[nid][0].next_id
                graph[nextid] = [e for e in graph[nextid] if e.next_id != nid]
                del graph[nid]
            elif len(graph[nid]) == 2: # inline any node that is just a pass through
                first, last = graph[nid]
                first_to = [e for e in graph[first.next_id] if e.next_id == nid][0]
                last_to = [e for e in graph[last.next_id] if e.next_id == nid][0]
                graph[first.next_id] = [e for e in graph[first.next_id] if e.next_id != nid] + [ACOEdge(last.next_id, first_to.cost+last.cost, first_to.interest+last.interest, first_to.rest or last_to.rest)]
                graph[last.next_id] = [e for e in graph[last.next_id] if e.next_id != nid] +[ACOEdge(first.next_id, last_to.cost+first.cost, last_to.interest+first.interest, first_to.rest or last_to.rest)]
                del graph[nid]
        stats = Counter(len(b) for b in graph.values())
    return graph
