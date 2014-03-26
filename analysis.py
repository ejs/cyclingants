class StubAnaliser:
    def __init__(self, graph):
        pass

    def generation(self, graph, gen):
        pass

    def step(self, graph, ants, gen, step):
        pass

    def result(self):
        return None

    def __str__(self):
        return "{}".format(self.result())


class TrackNodeVisits(StubAnaliser):
    def __init__(self, graph):
        self.nodes_visited = {nid:0 for nid in graph}

    def step(self, graph, ants, gen, step):
        for a in ants:
            self.nodes_visited[a.position] += 1

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
        self.marked = 0
        self.turns = 0

    def generation(self, graph, gen):
        self.turns += 1
        self.total += sum(e.pheromones for n in graph for e in graph[n])/sum(1 for n in graph for e in graph[n])
        self.marked += sum(e.pheromones for n in graph for e in graph[n])/(sum(1 for n in graph for e in graph[n] if e.pheromones) or 1)

    def result(self):
        return self.total/self.turns, self.marked/self.turns

    def __str__(self):
        return "Average pheromone concentration {} marked only {}".format(*self.result())


class TrackInterest(StubAnaliser):
    def __init__(self, graph):
        self.turns = 0
        self.total = 0

    def step(self, graph, ants, gen, step):
        if ants:
            self.turns += 1
            self.total += sum(a.interest for a in ants)/len(ants)

    def result(self):
        return self.total/self.turns

    def __str__(self):
        return "Average ant interest {}".format(self.result())


class Printer(StubAnaliser):
    def step(self, graph, ants, gen, step):
        if not step%1000:
            print(gen, step, len(ants))

    def generation(self, graph, gen):
        print(gen)
