#! /usr/bin/python3
"""
    Usage:
        main.py osm <inputfile> <outputfile>
        main.py pickle <inputfile> <outputfile>
"""
from collections import defaultdict, Counter

from aco import run_on_graph, BasicAnt, ACOEdge
import analysis
from display import GPXOutput
from graphsearch import analyse_graph, find_most_connected_node
from osm import load_file
import waysdb


def ways_to_graph(ways):
    graph = defaultdict(list)
    for way in ways:
        nds = way['nodes']
        for start, middle, end in zip(nds, nds[1:], nds[2:]+[None]):
            if not start.intersection:
                continue
            if middle.intersection:
                interest = start.interest + middle.interest
                rest = start.rest or middle.start
                graph[start.nid].append(ACOEdge(middle.nid, start.cost_to(*middle.start), interest, rest))
                graph[middle.nid].append(ACOEdge(start.nid, middle.cost_to(*start.stop), interest, rest))
            elif end:
                interest = start.interest + middle.interest + end.interest
                rest = start.rest or middle.rest or end.rest
                graph[start.nid].append(ACOEdge(end.nid, start.cost_to(*middle.start)+middle.cost_out+end.cost_from(*middle.stop), interest, rest))
                graph[end.nid].append(ACOEdge(start.nid, end.cost_to(*middle.stop)+middle.cost_back+start.cost_from(*middle.start), interest, rest))
    return graph


def clean_graph(graph):
    stats = Counter(len(b) for b in graph.values())
    while stats[1] or stats[0] or stats[2]:
        for nid in list(graph.keys()):
            if len(graph[nid]) == 0: # remove anything that has been emptied
                del graph[nid]
            elif len(graph[nid]) == 1: # remove dead ends
                nextid = graph[nid][0].next_id
                graph[nextid] = [e for e in graph[nextid] if e.next_id != nid]
                del graph[nid]
            elif len(graph[nid]) == 2: # inline any node that is just a pass through
                first, last = graph[nid]
                first_to = [e for e in graph[first.next_id] if e.next_id == nid][0]
                last_to = [e for e in graph[last.next_id] if e.next_id == nid][0]
                graph[first.next_id] = [e for e in graph[first.next_id] if e.next_id != nid] + [ACOEdge(last.next_id, first_to.cost+last.cost, first_to.interest+last.interest, first_to.rest or last_to.rest)]
                graph[last.next_id] = [e for e in graph[last.next_id] if e.next_id != nid] +[ACOEdge(first.next_id, last_to.cost+first.cost, last_to.interest+first.interest, first_to.rest or last_to.rest)]
                del graph[nid]
        stats = Counter(len(b) for b in graph.values())
    return graph


def set_up_analyisis(graph):
    return [analysis.Printer(graph),
            analysis.TrackNodeVisits(graph),
            analysis.PheromoneConcentration(graph),
            analysis.TrackInterest(graph),
            analysis.Distance(graph)]


def display(graph, ways, filename):
    sink = GPXOutput()
    for w in ways:
        for n in w['nodes']:
            sink.add_track([n.start, n.stop])
    sink.save_to_file(filename)


if __name__ == '__main__':
    from docopt import docopt
    arguments = docopt(__doc__, version="Cycling Ants 0.1")
    if arguments['osm']:
        ways = load_file(arguments['<inputfile>'])
    elif arguments['pickle']:
        from osm import RouteSection
        ways = waysdb.load(arguments['<inputfile>'])
    graph = clean_graph(ways_to_graph(ways))
    analyse_graph(graph)
    starting_points = find_most_connected_node(graph)
    analyisis = set_up_analyisis(graph)
    try:
        result = run_on_graph(graph, starting_points, 200, 5, lambda p: BasicAnt(p, 100, 30), *analyisis)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Something broke")
        print(e)
        print()
    else:
        display(graph, ways, arguments['<outputfile>'])
    if analysis:
        print()
        for a in analyisis:
            try:
                res = "{}".format(a)
                if res != "None":
                    print(res)
            except:
                pass
