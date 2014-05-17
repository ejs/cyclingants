import csv


class StubAnaliser:
    def __init__(self, graph):
        pass

    def __call__(self, graph, gen, ants):
        return []

    def result(self):
        return None

    def __bool__(self):
        return self.result() is not None

    def __str__(self):
        return "{}".format(self.result())

    def row_headers(self):
        return []


class CSVWrapper(StubAnaliser):
    def __init__(self, filename, subanalysers):
        self.sink = csv.writer(open(filename, 'w'))
        self.analysers = subanalysers
        self.sink.writerow([h for a in self.analysers for h in a.row_headers()])

    def __call__(self, graph, gen, ants):
        self.sink.writerow([c for a in self.analysers for c in a(graph, gen, ants)])

    def __bool__(self):
        return any(self.analysers)

    def __str__(self):
        return "\n".join(self.sub_strings())

    def sub_strings(self):
        for a in self.analysers:
            if a:
                try:
                    yield str(a)
                except Exception as e:
                    print(a, e)
                    pass

    def close(self):
        self.sink.close()


class TrackNodeVisits(StubAnaliser):
    def __init__(self, graph):
        self.nodes_visited = {nid:0 for nid in graph}

    def row_headers(self):
        return ["Nodes visited", "Total Nodes"]

    def __call__(self, graph, gen, ants):
        for a in ants:
            for n in a.moves:
                self.nodes_visited[n] += 1
        visited = sum(1 for n, v in self.nodes_visited.items() if v)
        total = len(self.nodes_visited)
        return [visited, total]

    def result(self):
        return self.nodes_visited

    def __str__(self):
        visited = sum(1 for n, v in self.nodes_visited.items() if v)
        total = len(self.nodes_visited)
        return "{} visited out of {}".format(visited, total)


class PheromoneConcentration(StubAnaliser):
    def __init__(self, graph):
        self.total = 0
        self.turns = 0

    def row_headers(self):
        return ["Average pheromones", "Max Pheromones"]

    def __call__(self, graph, gen, ants):
        self.turns += 1
        self.total += sum(e.pheromones for _, _, e in graph.get_edges())/sum(1 for _ in graph.get_edges())
        a = sum(e.pheromones for _, _, e in graph.get_edges())/sum(1 for e in graph.get_edges())
        m =max(e.pheromones for _, _, e in graph.get_edges())
        print("Average pheromones", a)
        print("Max pheromones", m)
        return [a, m]

    def result(self):
        return self.total/self.turns

    def __str__(self):
        return "Average pheromone concentration {}".format(self.result())


class Printer(StubAnaliser):
    def __call__(self, graph, gen, ants):
        print()
        print("Generation", gen+1)
        return []


class TrackInterest(StubAnaliser):
    def row_headers(self):
        return ['average interest', 'max interest']

    def __call__(self, graph, gen, ants):
        av = sum(a.interest for a in ants)/len(ants)
        m = max(a.interest for a in ants)
        print("average interest", av)
        print("max interest", m)
        return [av, m]


class Distance(StubAnaliser):
    def row_headers(self):
        return ["longest distance", "total distance", "average distance"]

    def __call__(self, graph, gen, ants):
        l = max(a.age for a in ants)
        t = sum(a.age for a in ants)
        a = sum(a.age for a in ants)/len(ants)
        print("longest distance", l)
        print("total distance", t)
        print("average distance", a)
        return [l, t, a]


def GraphOverview(graph):
    print(graph)
    print("Rest edges", sum(1 for _, _, e in graph.get_edges() if e.rest))
    print("Rest nodes", sum(1 for n in graph if graph.get_node(n).rest))
    print("Interesting edges", sum(1 for _, _, e in graph.get_edges() if e.interest))
    print("Interesting nodes", sum(1 for n in graph if graph.get_node(n).interest))
    print("Connected components", graph.connected_components())
    print("Longest edge", max(e.cost_out for _, _, e in graph.get_edges()))
