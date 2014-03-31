from collections import Counter

from sizing import total_size


class StubAnaliser:
    def __init__(self, graph):
        pass

    def generation(self, graph, gen, ants):
        pass

    def result(self):
        return None

    def __str__(self):
        return "{}".format(self.result())


class TrackNodeVisits(StubAnaliser):
    def __init__(self, graph):
        self.nodes_visited = {nid:0 for nid in graph}

    def generation(self, graph, gen, ants):
        for a in ants:
            for n in a.moves:
                self.nodes_visited[n] += 1

    def result(self):
        return self.nodes_visited

    def __str__(self):
     return "{} visited out of {}".format(sum(1 for n in self if self[n]), len(self))

    def __iter__(self):
        return iter(self.nodes_visited)

    def __getitem__(self, key):
        return self.nodes_visited[key]

    def __len__(self):
        return len(self.nodes_visited)


class PheromoneConcentration(StubAnaliser):
    def __init__(self, graph):
        self.total = 0
        self.turns = 0

    def generation(self, graph, gen, ants):
        self.turns += 1
        self.total += sum(e.pheromones for n in graph for e in graph[n])/sum(1 for n in graph for e in graph[n])
        print("Average pheromones", sum(e.pheromones for n in graph for e in graph[n])/sum(1 for n in graph for e in graph[n]))
        print("Max pheromones", max(e.pheromones for n in graph for e in graph[n]))

    def result(self):
        return self.total/self.turns

    def __str__(self):
        return "Average pheromone concentration {}".format(self.result())


class Printer(StubAnaliser):
    def generation(self, graph, gen, ants):
        print()
        print("Generation", gen)


class TrackInterest(StubAnaliser):
    def generation(self, graph, gen, ants):
        print("average interest", sum(a.interest for a in ants)/len(ants))
        print("max interest", max(a.interest for a in ants))


class Distance(StubAnaliser):
    def generation(self, graph, gen, ants):
        print("longest distance", max(a.age for a in ants))
        print("total distance", sum(a.age for a in ants))
        print("average distance", sum(a.age for a in ants)/len(ants))


class GraphOverview(StubAnaliser):
    def __init__(self, graph):
        print("Size {0:,d}kb".format(total_size(graph)//1024))
        print("Nodes", len(graph))
        print("Edges", sum(len(e) for e in graph.values()))
        print("Rest edges", sum(1 for e in graph.values() for n in e if n.rest))
        print("Interesting edges", sum(1 for e in graph.values() for n in e if n.interest))
        print("Total interestingness", sum(n.interest for e in graph.values() for n in e))
        print("Stats", Counter(len(e) for e in graph.values()))
        print("Connected components", self.is_connected(graph))
        print("Longest edge", max(e.cost for edges in graph.values() for e in edges))

    def is_connected(self, graph):
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
