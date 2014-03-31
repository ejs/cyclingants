#! /usr/bin/python3
"""
    Usage:
        main.py osm <inputfile> <outputfile>
        main.py pickle <inputfile> <outputfile>
"""
from collections import defaultdict

from aco import run_on_graph, BasicAnt, ACOEdge
import analysis
from display import GPXOutput
import graphtools


def ways_to_locations(ways):
    return {(n.nid if n.intersection else n.nid[0]):n.start for w in ways for n in w['nodes']}


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


def set_up_analyisis(graph):
    return [analysis.GraphOverview(graph),
            analysis.Printer(graph),
            analysis.TrackNodeVisits(graph),
            analysis.PheromoneConcentration(graph),
            analysis.TrackInterest(graph),
            analysis.Distance(graph)]


def display_analysis(analysis):
    if analysis:
        print()
        for a in analyisis:
            try:
                res = "{}".format(a)
                if res != "None":
                    print(res)
            except:
                pass


def display(graph, ways, start, filename):
    pos = ways_to_locations(ways)
    sink = GPXOutput()
    sink.add_points(*list({p for w in ways for n in w['nodes'] for p in (n.start, n.stop)}))
    sink.add_track([pos[n] for n in graphtools.most_marked_route(graph, start)])
    sink.save_to_file(filename)


def load_graph(config):
    # TODO: check to see if I can use docopt to avoid manipulating the imports like this
    if config['osm']:
        import osm as source
    elif config['pickle']:
        import waysdb as source
    ways = source.load_file(config['<inputfile>'])
    return graphtools.clean_graph(ways_to_graph(ways)), ways


if __name__ == '__main__':
    from docopt import docopt
    from osm import RouteSection # shim for pickle
    config = docopt(__doc__, version="Cycling Ants 0.1")
    graph, ways = load_graph(config)
    starting_points = graphtools.find_most_connected_node(graph)
    analyisis = set_up_analyisis(graph)
    try:
        AntFactory = lambda p: BasicAnt(p, 100, 30)
        result = run_on_graph(graph, starting_points, 20, 5, AntFactory, *analyisis)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Something broke")
        print(e)
        print()
    else:
        display(graph, ways, starting_points[0], config['<outputfile>'])
    display_analysis(analysis)
