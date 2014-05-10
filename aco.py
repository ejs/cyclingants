#! /usr/bin/python3
from bisect import bisect
from collections import Counter
from itertools import accumulate, starmap
from random import choice, random


class ACOEdge:
    def __init__(self, cost, interest, rest):
        self.cost = cost
        self.interest = interest
        self.pheromones = 1
        self.rest = rest

class Swarm:
    def __init__(self, size, max_age, max_tiredness, alpha, beta, evaporation, Ant):
       self.max_age = max_age
       self.max_tiredness = max_tiredness
       self.size = size
       self.alpha = alpha
       self.beta = beta
       self.Ant = Ant
       self.evaporation = evaporation

    def run_generation(self, graph, starting_points):
        for _ in range(self.size):
            ant = self.Ant(choice(starting_points), self.max_age, self.max_tiredness, self.alpha, self.beta)
            ant(graph)
            yield ant

    def __call__(self, graph, starting_points, rounds, *analytics):
        for i in range(rounds):
            ants = list(self.run_generation(graph, starting_points))
            self.deposit(graph, ants)
            self.evaporate(graph)
            for an in analytics:
                an.generation(graph, i, ants)
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
        self.last_position = None
        self.moves = [position]
        self.max_age = max_age
        self.max_tiredness = max_tiredness
        self.age = 0
        self.tiredness = 0
        self.interest = 0
        self.alpha = alpha
        self.beta = beta

    def __call__(self, graph):
        self.travel(graph)
        self.simplify_journy()
        self.age = sum(graph.get_edges(a, b)[0].cost for a, b in self)
        self.interest = sum(graph.get_edges(a, b)[0].interest for a, b in self) + sum(graph[a].interest for a, _ in self)

    def travel(self, graph):
        try:
            while self.age < self.max_age and self.tiredness < self.max_tiredness:
                next_id, next_node, edge_traveled = self.pick_next(graph)
                self.age += edge_traveled.cost
                if edge_traveled.rest or next_node.rest:
                    self.tiredness = 0
                else:
                    self.tiredness += edge_traveled.cost
                self.last_position = self.moves[-1]
                self.moves.append(next_id)
        except IndexError:
            pass

    def pick_next(self, graph):
        valid_choices = [(to, graph[to], e)
            for to, e in graph.get_edges(self.moves[-1])
                if to != self.last_position]
        choice = biased_random(starmap(self.evaluate_edge, valid_choices))
        return valid_choices[choice]

    def simplify_journy(self):
        node_visits = Counter(self.moves)
        while node_visits.most_common(1)[0][1] > 1:
            # I'm not sure how this can need doing more than once but apparently it can
            skipping_till = None
            loopless = []
            for n in self.moves:
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
            self.moves = loopless
            node_visits = Counter(self.moves)

    def __iter__(self):
        for a, b in zip(self.moves, self.moves[1:]):
            yield a, b

    def evaluate_route(self):
        return self.interest*(self.age/self.max_age)

    def evaluate_edge(self, next_id, next_node, edge):
        return edge.pheromones**self.alpha * (next_node.interest+edge.interest+(1 if edge.rest or next_node.rest else 0)+1)**self.beta


def biased_random(chances):
    """ Makes use of pattern from http://docs.python.com/3.3/library/random """
    cumulative_dis = list(accumulate(chances))
    roll = random() * cumulative_dis[-1]
    return bisect(cumulative_dis, roll) if roll else 0
