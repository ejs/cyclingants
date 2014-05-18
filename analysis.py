import csv


class StubAnaliser:
    """ Provide basic functionality of a full analyser

        if this is to be used with CSVWrapper or similar
        it must return the same length list whenever row_headers
        and __call__ are called
    """
    def __init__(self, graph):
        """ Initialise with the graph that will be analysed by this"""
        pass

    def row_headers(self):
        """ Returns a header description of the results returned by __call__ """
        return []

    def __call__(self, graph, gen, ants):
        """ Analyse the results of a single generation searching the graph

            graph   the state of the graph at the end of the generation
            gen     the generation number (starting from 0)
            ants    the final state of all ants from this generation

            returns a list of any relevant results from this generation
        """
        return []

    def result(self):
        """ Any displayable final result of the analysis"""
        return None

    def __bool__(self):
        """ If there is any final result of this analysis"""
        return self.result() is not None

    def __str__(self):
        """ A displayable summary string of this analysis"""
        return "{}".format(self.result())


class CSVWrapper(StubAnaliser):
    """ Wraps a collection of analysers and outputs there results to a CSV file

        filename        the name of the file to save the CSV data to
        stubanalysers   analysis callables expected to provide at least
                        an extra row_headers() method

        Whenever this is called each of the subanalysers is also called
        and a row is written to the CSV file containing the results
    """
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
    """ Tracks and reports

            The number of nodes that were visited this generation
            The number of nodes that have ever been visited
            The total number of nodes in the graph (for context)
    """
    def __init__(self, graph):
        self.nodes_visited = {nid:0 for nid in graph}

    def row_headers(self):
        return ["Nodes ever visited", "Nodes visited this time", "Total Nodes"]

    def __call__(self, graph, gen, ants):
        gen_visits = set()
        for a in ants:
            for n in a.moves:
                self.nodes_visited[n] += 1
                gen_visits.add(n)
        visited = sum(1 for n, v in self.nodes_visited.items() if v)
        total = len(self.nodes_visited)
        return [visited, len(gen_visits), total]

    def result(self):
        return self.nodes_visited

    def __str__(self):
        visited = sum(1 for n, v in self.nodes_visited.items() if v)
        total = len(self.nodes_visited)
        return "{} visited out of {}".format(visited, total)


class StatisticalAnalyser(StubAnaliser):
    """ Report about the quantity of something every generation

        Reports
            Minimum single value
            Average value
            Maximum single value
    """
    def row_headers(self):
        return ["Min "+self.name, "Average "+self.name, "Max "+self.name]

    def examine(self, ants, graph):
        raise NotImplimentedError()

    def __call__(self, graph, gen, ants):
        mi = min(self.examine(ants, graph))
        a = sum(self.examine(ants, graph))/sum(1 for _ in self.examine(ants, graph))
        m = max(self.examine(ants, graph))
        print("Average "+self.name, a)
        return [mi, a, m]


class PheromoneConcentration(StatisticalAnalyser):
    """ Report on the global amount of pheromone on the map.

        Reports
            Minimum single concentration
            Average level
            Maximum single concentration
    """
    name = "pheromones"

    def examine(self, ants, graph):
        for _, _, e in graph.get_edges():
            yield e.pheromones


class Printer(StubAnaliser):
    """ Prints out a header, no reporting"""
    def __call__(self, graph, gen, ants):
        print()
        print("Generation", gen+1)
        return []


class TrackInterest(StatisticalAnalyser):
    """ Reports on the quality of routes seached this generation

        Reports
            minimum interest of all routes
            average interest of all routes
            Maximum interest of any route
    """
    name = "interest"
    
    def examine(self, ants, graph):
        for a in ants:
            yield a.interest


class Distance(StatisticalAnalyser):
    """ Reports on the length of routes (in km) searched this generation

        Reports
            minimum length of any route
            average length of all routes
            Maximum length of any route
    """
    name = "distance"

    def examine(self, ants, graph):
        for a in ants:
            yield a.age


class StepsTaken(StatisticalAnalyser):
    """ Reports on the length of routes (in edges) searched this generation

        Reports
            minimum length of any route
            average length of all routes
            Maximum length of any route
    """
    name = "steps"

    def examine(self, ants, graph):
        for a in ants:
            yield len(a.moves)


def GraphOverview(graph):
    """ Provide some basic information on the graph about to be searched"""
    print(graph)
    print("Rest edges", sum(1 for _, _, e in graph.get_edges() if e.rest))
    print("Rest nodes", sum(1 for n in graph if graph.get_node(n).rest))
    print("Interesting edges", sum(1 for _, _, e in graph.get_edges() if e.interest))
    print("Interesting nodes", sum(1 for n in graph if graph.get_node(n).interest))
    print("Connected components", graph.connected_components())
    print("Longest edge", max(e.cost_out for _, _, e in graph.get_edges()))
