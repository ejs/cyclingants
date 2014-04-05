#! /usr/bin/python3
from bisect import bisect
from collections import Counter
from itertools import accumulate
from random import choice, random


class ACOEdge:
    __slots__ = ["next_id", "cost", "interest", "pheromones", "rest"]
    p = 0.99 # TODO: tweak this
    # Question: should this be linked to the ants?

    def __init__(self, nid, cost, interest, rest):
        self.next_id = nid
        self.cost = cost
        self.interest = interest
        self.pheromones = 1
        self.rest = rest

    def evaporate(self):
        self.pheromones *= self.p

    def deposit(self, amount):
        self.pheromones += amount


class BasicAnt:
    # TODO: tweak these
    alpha = 1
    beta = 2

    def __init__(self, position, max_age, max_tiredness):
        self.position = position
        self.last_position = None
        self.moves = [position]
        self.max_age = max_age
        self.max_tiredness = max_tiredness
        self.age = 0
        self.tiredness = 0
        self.interest = 0
        self.dead = False

    def search(self, graph):
        while self.alive():
            self.move(graph)
        self.simplify_journy(graph)

    def move(self, graph):
        try:
            next_position = self.pick_next(graph)
        except IndexError:
            self.dead = True
        else:
            self.last_position = self.position
            self.age += next_position.cost
            self.tiredness = 0 if next_position.rest else self.tiredness+next_position.cost
            self.interest += next_position.interest
            self.position = next_position.next_id
            self.moves.append(next_position.next_id)
        return self

    def pick_next(self, graph):
        valid_choices = [e for e in graph[self.position] if e.next_id != self.last_position]
        return valid_choices[biased_random(map(self.evaluate, valid_choices))]

    def simplify_journy(self, graph):
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
            self.age = sum(e.cost for a, b in self for e in graph[a] if e.next_id == b)
            self.interest = sum(e.interest for a, b in self for e in graph[a] if e.next_id == b)
            node_visits = Counter(self.moves)

    def __iter__(self):
        for a, b in zip(self.moves, self.moves[1:]):
            yield a, b

    def deposition(self):
        return self.interest*(self.age/self.max_age)

    def alive(self):
        return not self.dead and self.age < self.max_age and self.tiredness < self.max_tiredness

    def evaluate(self, edge):
        if edge.next_id == self.last_position:
            return 0 # No interest in returning to the last position
        return edge.pheromones**self.alpha * (edge.interest+(1 if edge.rest else 0)+1)**self.beta


class LooplessAnt(BasicAnt):
    """ It appears that the decreased exploration completely counters any
        increase in the theoretical value of of the final route
        as the chance of any ant finding any point of interest is
        close to 0
    """
    def evaluate(self, edge):
        if edge.next_id in self.moves:
            return 0 # No interest in looping
        return super().evaluate(edge)

    def pick_next(self, graph):
        valid_choices = [e for e in graph[self.position] if e.next_id not in self.moves]
        if not valid_choices:
            raise ValueError
        return valid_choices[biased_random(map(self.evaluate, valid_choices))]

    def deposit(self):
        return (1+self.interest)*(self.age/self.max_age)


def biased_random(chances):
    """ Makes use of pattern from http://docs.python.com/3.3/library/random """
    cumulative_dis = list(accumulate(chances))
    roll = random() * cumulative_dis[-1]
    return bisect(cumulative_dis, roll) if roll else 0


def run_ant(Ant, graph, starting_point):
    a = Ant(starting_point)
    a.search(graph)
    return a


def run_on_graph(graph, starting_points, number_of_ants, rounds, Ant, *analytics):
    for i in range(rounds):
        ants = [run_ant(Ant, graph, choice(starting_points)) for i in range(number_of_ants)]
        for edges in graph.values():
            for edge in edges:
                edge.evaporate()
        for ant in ants:
            for a, b in ant:
                for edge in graph[a]:
                    if edge.next_id == b:
                        edge.deposit(ant.deposition())
        for an in analytics:
            an.generation(graph, i, ants)
    return graph
