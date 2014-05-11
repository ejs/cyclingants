#! /usr/bin/python3
"""
    Usage:
        main.py osm <osmfile> [<gpxfile>]
        main.py makepickle <osmfile> <picklefile>
        main.py usepickle <picklefile> [<gpxfile>]
"""
from aco import BasicAnt, Swarm
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
        distance += edge[1].cost_out


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


def graph_to_gpx(graph, config):
    max_distance = 200
    starting_points = graph.find_most_connected_nodes()
    print("start", starting_points)
    evaluation = set_up_analyisis(graph)
    swarm = Swarm(100, max_distance, 100, 1, 2, 0.75, BasicAnt)
    try:
        result = swarm(graph, starting_points, 20, *evaluation)
    except KeyboardInterrupt:
        pass
    else:
        display_analysis(evaluation)
        if config['<gpxfile>']:
            display(config['<gpxfile>'], result, starting_points[0], distance=max_distance)


def osmtogpx(config):
    osmgraph = osm.load_graph(config['<osmfile>'])
    graph_to_gpx(osmgraph, config)


def osmtopickle(config, picklefile):
    osmgraph = osm.load_graph(config['<osmfile>'])
    if picklefile:
        waysdb.store_graph(osmgraph, picklefile)


def pickletogpx(config):
    osmgraph = waysdb.load_graph(config['<picklefile>'])
    graph_to_gpx(osmgraph, config)


if __name__ == '__main__':
    from docopt import docopt
    config = docopt(__doc__, version="Cycling Ants 0.1")
    if config['osm']:
        osmtogpx(config)
    elif config['makepickle' ]:
        osmtopickle(config)
    elif config['usepickle']:
        pickletogpx(config)
