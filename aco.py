#! /usr/bin/python3
from bisect import bisect
from collections import Counter
from itertools import accumulate, starmap
from random import choice, random


class PheromoneWrapper:
    def __init__(self, wraps):
        self.pheromones = 1
        self.wraps = wraps

    def __getattr__(self, name):
        return getattr(self.wraps, name)


class Swarm:
    def __init__(self, size, max_age, max_tiredness, alpha, beta, evaporation, Ant):
        self.max_age = max_age
        self.max_tiredness = max_tiredness
        self.size = size
        self.alpha = alpha
        self.beta = beta
        self.Ant = Ant
        self.evaporation = evaporation

    def setup_graph(self, graph):
        return graph.transform(t_edge=PheromoneWrapper)

    def run_generation(self, graph, starting_points):
        for _ in range(self.size):
            ant = self.Ant(choice(starting_points), self.max_age, self.max_tiredness, self.alpha, self.beta)
            ant(graph)
            yield ant

    def __call__(self, graph, starting_points, rounds, *analytics):
        graph = self.setup_graph(graph)
        for i in range(rounds):
            ants = list(self.run_generation(graph, starting_points))
            self.deposit(graph, ants)
            self.evaporate(graph)
            for an in analytics:
                an(graph, i, ants)
        return graph

    def deposit(self, graph, ants):
        for ant in ants:
            deposition = ant.evaluate_route()
            for a, b in ant:
                for edge in graph.get_edges(a, b):
                    edge.pheromones += deposition

    def evaporate(self, graph):
        for _, _, edge in graph.get_edges():
            edge.pheromones *= self.evaporation


class BasicAnt:
    def __init__(self, position, max_age, max_tiredness, alpha, beta):
        self.moves = [position]
        self.max_age = max_age
        self.max_tiredness = max_tiredness
        self.alpha = alpha
        self.beta = beta
        self.age = 0
        self.interest = 0

    def __call__(self, graph):
        self.travel(graph)
        self.moves = self.simplify_journy(self.moves)
        self.age = sum(graph.get_edges(a, b)[0].cost_out for a, b in self)
        self.interest = sum(graph.get_edges(a, b)[0].interest+graph[a].interest for a, b in self)

    def travel(self, graph):
        try:
            age, tiredness = 0, 0
            last = None
            while age < self.max_age and tiredness < self.max_tiredness:
                nid, node, edge = self.pick_next(graph, last, self.moves[-1])
                age += edge.cost_out
                tiredness = 0 if edge.rest or node.rest else tiredness+edge.cost_out
                last = self.moves[-1]
                self.moves.append(nid)
        except IndexError:
            pass

    def pick_next(self, graph, last, current):
        valid_choices = [(to, graph[to], e) for to, e in graph.get_edges(current) if to != last]
        choice = biased_random(starmap(self.evaluate_edge, valid_choices))
        return valid_choices[choice]

    def simplify_journy(self, moves):
        node_visits = Counter(moves)
        while node_visits.most_common(1)[0][1] > 1:
            skipping_till = None
            loopless = []
            for n in moves:
                if not skipping_till:
                    if node_visits[n] > 1:
                        skipping_till = n
                    else:
                        loopless.append(n)
                else:
                    if n == skipping_till:
                        loopless.append(n)
                        skipping_till = None
                        node_visits[n] -= 2
                    else:
                        node_visits[n] -= 1
            moves = loopless
            node_visits = Counter(moves)
        return moves

    def __iter__(self):
        for a, b in zip(self.moves, self.moves[1:]):
            yield a, b

    def evaluate_route(self):
        return self.interest*(self.age/self.max_age)

    def evaluate_edge(self, next_id, next_node, edge):
        local_interest = 1+next_node.interest+edge.interest+(1 if edge.rest or next_node.rest else 0)
        return edge.pheromones**self.alpha * local_interest**self.beta


def biased_random(chances):
    """ Makes use of pattern from http://docs.python.com/3.3/library/random """
    cumulative_dis = list(accumulate(chances))
    roll = random() * cumulative_dis[-1]
    return bisect(cumulative_dis, roll) if roll else 0
