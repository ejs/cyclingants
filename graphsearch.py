from collections import Counter

from sizing import total_size


def is_connected(graph):
    """ Use union find to check whole graph in linear time"""
    nodes = {nid:None for nid in graph}
    for node, edges in graph.items():
        for nextnode in edges:
            nextnid = nextnode.next_id
            while nodes[node]:
                node = nodes[node]
            while nodes[nextnid]:
                nextnid = nodes[nextnid]
            if node != nextnid:
                nodes[node] = nextnid
    return sum(1 for parent in nodes.values() if not parent)


def find_most_connected_node(graph):
    most_connected, starting_points = 0, []
    for node, edges in graph.items():
        if len(edges) > most_connected:
            most_connected = len(edges)
            starting_points = [node]
        elif len(edges) == most_connected:
            starting_points.append(node)
    return starting_points


def analyse_graph(graph):
    print("Size {0:,d}kb".format(total_size(graph)//1024))
    print("Nodes", len(graph))
    print("Edges", sum(len(e) for e in graph.values()))
    print("Rest edges", sum(1 for e in graph.values() for n in e if n.rest))
    print("Interesting edges", sum(1 for e in graph.values() for n in e if n.interest))
    print("Total interestingness", sum(n.interest for e in graph.values() for n in e))
    print("Stats", Counter(len(e) for e in graph.values()))
    print("Connected components", is_connected(graph))
    print("Longest edge", max(e.cost for edges in graph.values() for e in edges))
