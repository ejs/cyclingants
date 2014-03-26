#! /usr/bin/python3
from bisect import bisect
from collections import namedtuple
from itertools import accumulate, count
from random import choice, random


class ACOEdge:
    __slots__ = ["next_id", "cost", "interest", "pheromones", "rest"]

    def __init__(self, nid, cost, interest, rest):
        self.next_id = nid
        self.cost = cost
        self.interest = interest
        self.pheromones = 1
        self.rest = rest

    def evaporate(self):
        self.pheromones *= 0.5

    def deposit(self, amount):
        self.pheromones += amount


class BasicAnt():
    def __init__(self, position, max_age, max_tiredness):
        self.position = position
        self.last_position = None
        self.moves = [position]
        self.max_age = max_age
        self.max_tiredness = max_tiredness
        self.age = 0
        self.tiredness = 0
        self.interest = 0

    def move(self, graph):
        try:
            next_position = self.pick_next(graph)
        except:
            self.age = self.max_age # die
        else:
            self.last_position = self.position
            self.age += next_position.cost
            if next_position.rest:
                self.tiredness = 0
            else:
                self.tiredness += next_position.cost
            self.interest += next_position.interest
            self.position = next_position.next_id
            self.moves.append(next_position.next_id)
        return self

    def pick_next(self, graph):
        """ Makes use of pattern from http://docs.python.com/3.3/library/random """
        valid_choices = [e for e in graph[self.position] if e.next_id != self.last_position]
        cumulative_dis = list(accumulate(self.evaluate(e) for e in valid_choices))
        roll = random() * cumulative_dis[-1]
        if roll:
            return valid_choices[bisect(cumulative_dis, roll)]
        else: # Apparently bisect breaks on 0
            return valid_choices[0]

    def trail(self):
        for a, b in zip(self.moves, self.moves[1:]):
            yield a, b

    def deposition(self):
        return self.interest*(self.age/self.max_age)

    def alive(self):
        return self.age < self.max_age and self.tiredness < self.max_tiredness

    def evaluate(self, edge):
        if edge.next_id == self.last_position:
            return 0 # No interest in returning to the last position
        # TODO: tweak this
        return edge.pheromones**2 * (edge.interest+(1 if edge.rest else 0)+1)**2


def run_ant(Ant, graph, starting_point):
    a = Ant(starting_point)
    while a.alive():
        a.move(graph)
    return a


def run_on_graph(graph, starting_points, number_of_ants, rounds, Ant, *analytics):
    for i in range(rounds):
        ants = [run_ant(Ant, graph, choice(starting_points)) for i in range(number_of_ants)]
        for edges in graph.values():
            for edge in edges:
                edge.evaporate()
        for ant in ants:
            for a, b in ant.trail():
                for edge in graph[a]:
                    if edge.next_id == b:
                        edge.deposit(ant.deposition())
        for an in analytics:
            an.generation(graph, i, ants)
    return graph
