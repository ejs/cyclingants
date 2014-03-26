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
        self.pheromones = 0
        self.rest = rest

    def evaporate(self):
        self.pheromones *= 0.9 # TODO: better decay

    def deposit(self, amount):
        self.pheromones += amount


class BasicAnt():
    def __init__(self, position, max_age, max_tiredness):
        self.position = position
        self.last_position = None
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
            self.interest *= 0.9 # TODO: better interest decay
            self.interest += next_position.interest
            self.position = next_position.next_id
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

    def deposition(self):
        return 1 # TODO better deposit amount

    def alive(self):
        return self.age < self.max_age and self.tiredness < self.max_tiredness

    def evaluate(self, edge):
        if edge.next_id == self.last_position:
            return 0 # No interest in returning to the last position
        # TODO: tweak this
        return edge.pheromones**2 + (edge.interest+(1 if edge.rest else 0)+1)**2


def run_on_graph(graph, starting_points, number_of_ants, rounds, Ant, *analytics):
    for i in range(rounds):
        for an in analytics:
            an.generation(graph, i)
        ants = [Ant(choice(starting_points)) for i in range(number_of_ants)]
        for j in count(1):
            if not ants:
                break
            ants = [a.move(graph) for a in ants if a.alive()]
            for an in analytics:
                an.step(graph, ants, i, j)
            for edges in graph.values():
                for e in edges:
                    e.evaporate()
            for ant in ants:
                for edge in graph[ant.position]:
                    if edge.next_id == ant.last_position:
                        edge.deposit(ant.deposition())
    return graph
