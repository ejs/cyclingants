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
from graph import Graph
import graphtools


def osm_graph_to_aco_graph(graph):
    def transform_edge(edge):
        return ACOEdge(edge.cost_out, edge.interest, edge.rest)

    g = graph.transform(t_edge=transform_edge)
    return g


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


def display(graph, start, distance, filename):
    sink = GPXOutput()
    sink.add_points(*list({p for w in ways for n in w['nodes'] for p in (n.start, n.stop)}))
    sink.add_track([pos[n] for n in graphtools.most_marked_route(graph, start, distance)])
    sink.save_to_file(filename)


def load_graph(config):
    # TODO: check to see if I can use docopt to avoid manipulating the imports like this
    if config['osm']:
        import osm as source
    elif config['pickle']:
        import waysdb as source
        from osm import RouteIntersection, RouteEdge
    return osm_graph_to_aco_graph(source.load_graph(config['<inputfile>']))


if __name__ == '__main__':
    from docopt import docopt
    config = docopt(__doc__, version="Cycling Ants 0.1")
    graph = load_graph(config)
    starting_points = graph.find_most_connected_nodes()
    print("start", starting_points)
    analyisis = set_up_analyisis(graph)
    max_distance = 100
    try:
        AntFactory = lambda p: BasicAnt(p, max_distance, 30)
        result = run_on_graph(graph, starting_points, 300, 20, AntFactory, *analyisis)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Something broke")
        print(e)
        print()
    else:
        display(graph, ways, starting_points[0], max_distance, config['<outputfile>'])
    display_analysis(analysis)
