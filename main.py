#! /usr/bin/python3
"""
    Usage:
        main.py osm <osmfile> [<gpxfile>]
        main.py makepickle <osmfile> <picklefile>
        main.py usepickle <picklefile> [<gpxfile>]
"""
from aco import run_on_graph, BasicAnt, ACOEdge
import analysis
from display import GPXOutput
import osm
import waysdb


def most_marked_route(graph, start, max_distance):
    visited = set()
    distance = 0
    node = start
    while distance < max_distance:
        yield node
        visited.add(node)
        try:
            options = [(n, e) for n, e in graph.get_edges(node) if n not in visited]
            edge = max(options, key=lambda e:e[1].pheromones)
        except ValueError: # if there are no good choices stop looking
            break
        node = edge[0]
        distance += edge[1].cost


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
    sink.add_track([graph.get_node(n).position for n in most_marked_route(graph, start, distance)])
    sink.save_to_file(filename)


def runOnGraph(graph, max_distance=100):
    starting_points = graph.find_most_connected_nodes()
    print("start", starting_points)
    evaluation = set_up_analyisis(graph)
    AntFactory = lambda p: BasicAnt(p, max_distance, 30)
    try:
        result = run_on_graph(graph, starting_points, 300, 1, AntFactory, *evaluation)
    except KeyboardInterrupt:
        pass
    else:
        display_analysis(evaluation)
        return graph, starting_points[0]
    return None


def osmtogpx(osmfile, gpxfile=None):
    osmgraph = osm.load_graph(osmfile)
    acograph = osm_graph_to_aco_graph(osmgraph)
    result = runOnGraph(acograph)
    if result and gpxfile:
        display(gpxfile, *result, max_distance=100)


def osmtopickle(osmfile, picklefile):
    osmgraph = osm.load_graph(osmfile)
    if picklefile:
        waysdb.store_graph(osmgraph, picklefile)


def pickletogpx(picklefile, gpxfile=None):
    osmgraph = waysdb.load_graph(picklefile)
    acograph = osm_graph_to_aco_graph(osmgraph)
    result = runOnGraph(acograph)
    if result and gpxfile:
        display(gpxfile, *result, max_distance=100)


if __name__ == '__main__':
    from docopt import docopt
    config = docopt(__doc__, version="Cycling Ants 0.1")
    if config['osm']:
        osmtogpx(config['<osmfile>'], config['<gpxfile>'])
    elif config['makepickle' ]:
        osmtopickle(config['<osmfile>'], config['<picklefile>'])
    elif config['usepickle']:
        pickletogpx(config['<picklefile>'], config['<gpxfile>'])
