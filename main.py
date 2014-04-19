#! /usr/bin/python3
"""
    Usage:
        main.py osm <osmfile> [<gpxfile>]
        main.py makepickle <osmfile> <picklefile>
        main.py usepickle <picklefile> [<gpxfile>]
"""
from collections import defaultdict

from aco import run_on_graph, BasicAnt, ACOEdge
import analysis
from display import GPXOutput
from graph import Graph
import graphtools
import osm
import waysdb


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
        for a in analysis:
            try:
                res = "{}".format(a)
                if res != "None":
                    print(res)
            except:
                pass


def display(filename, graph, start, distance):
    sink = GPXOutput()
    sink.add_track([graph.get_node(n).position for n in graphtools.most_marked_route(graph, start, distance)])
    sink.save_to_file(filename)


def runOnGraph(graph):
    starting_points = graph.find_most_connected_nodes()
    print("start", starting_points)
    evaluation = set_up_analyisis(graph)
    max_distance = 100
    AntFactory = lambda p: BasicAnt(p, max_distance, 30)
    try:
        result = run_on_graph(graph, starting_points, 300, 20, AntFactory, *evaluation)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Something broke")
        print(e)
        print()
    else:
        display_analysis(evaluation)
        return graph, starting_points[0], max_distance
    return None


def osmtogpx(osmfile, gpxfile=None):
    osmgraph = osm.load_graph(osmfile)
    acograph = osm_graph_to_aco_graph(osmgraph)
    result = runOnGraph(acograph)
    if result and gpxfile:
        display(gpxfile, *result)


def osmtopickle(osmfile, picklefile):
    osmgraph = osm.load_graph(osmfile)
    if picklefile:
        waysdb.store_graph(osmgraph, picklefile)


def pickletogpx(picklefile, gpxfile=None):
    osmgraph = waysdb.load_graph(picklefile)
    acograph = osm_graph_to_aco_graph(osmgraph)
    result = runOnGraph(acograph,)
    if result and gpxfile:
        display(gpxfile, *result)


if __name__ == '__main__':
    from docopt import docopt
    config = docopt(__doc__, version="Cycling Ants 0.1")
    if config['osm']:
        osmtogpx(config['<osmfile>'], config['<gpxfile>'])
    elif config['makepickle' ]:
        osmtopickle(config['<osmfile>'], config['<picklefile>'])
    elif config['usepickle']:
        pickletogpx(config['<picklefile>'], config['<gpxfile>'])
