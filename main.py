#! /usr/bin/python3
"""
    Usage:
        main.py (osm <osmfile> | pickle <picklefile>) [geo (<lat> <lon>)] [options] [<gpxfile>]
        main.py makepickle <osmfile> <picklefile>
        main.py -h | --help | --version

    -m <dist>, --max <dist>             Max distance [default: 300]
    -g <gen>, --generations <ge>        Number of Generations [default: 20]
    -s <size>, --size <size>            Swarm size [default: 50]
    -r <rest>, --rest <rest>            Rest period [default: 100]

    -a <alpha>, --alpha <alpha>         Alpha value for ACO [default: 1]
    -b <beta>, --beta <beta>            Beta value for ACD [default: 1]
    -e <evap>, --evaporation <evap>     Evaporation [default: 0.75]

    --halo <range>                      How far to project interesting points on to routes [default: 0.002]

    --analysisfile <file>               Where to store a CSV summary of what happened
"""

__version__ = "0.1"

from aco import BasicAnt, Swarm
import analysis
from display import GPXOutput
import osm
import waysdb


def most_marked_route(graph, start, max_distance):
    """ Build a route by following the strongest trail from the current location

        Total route length is limited by max_distance
        Nodes are not revisited
    """
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


def set_up_analyisis(graph, config):
    """ Create analysers and if set in config wrap in a CSVWrapper"""
    classes = [analysis.GraphOverview,
            analysis.Printer,
            analysis.TrackNodeVisits,
            analysis.PheromoneConcentration,
            analysis.TrackInterest,
            analysis.StepsTaken,
            analysis.Distance]
    analysers = [an for an in (a(graph) for a in classes) if an is not None]
    if analysers and config['--analysisfile']:
        return [analysis.CSVWrapper(config['--analysisfile'], analysers)]
    else:
        return analysers


def display_analysis(analysis):
    """ Print any final results of the analysis objects"""
    if analysis:
        print()
        for a in analysis:
            if a:
                try:
                    print("{}".format(a))
                except Exception as e:
                    print(e)


def display(filename, route):
    """ Draw the most marked trail as a gpx track """
    sink = GPXOutput()
    sink.add_track(route)
    sink.save_to_file(filename)


def build_swarm_from_config(config):
    """ Configure a swam to perform ACO using settings from the config"""
    size = int(config['--size'])
    max_distance = int(config['--max'])
    rest = int(config['--rest'])
    alpha = float(config['--alpha'])
    beta = float(config['--beta'])
    evaporation = float(config['--evaporation'])
    return Swarm(size, max_distance, rest, alpha, beta, evaporation, BasicAnt)


def graph_to_gpx(graph, config):
    """ Run and analyse an ACO search using parameters provided by config """
    max_distance = int(config['--max'])
    if config['geo']:
        starting_points = [(float(config['<lat>']), float(config['<lon>']))]
    else:
        starting_points = graph.find_most_connected_nodes()
    print("start", starting_points)
    evaluation = set_up_analyisis(graph, config)
    swarm = build_swarm_from_config(config)
    generations = int(config['--generations'])
    spot_best = analysis.PreserveBest(graph)
    try:
        result = swarm(graph, starting_points, generations, spot_best, *evaluation)
    except KeyboardInterrupt:
        pass
    else:
        display_analysis(evaluation)
        if config['<gpxfile>']:
            display(config['<gpxfile>'], spot_best.best[-1])


def osmtogpx(config):
    """ Perform an ACO search on OSM data to generate a GPX track"""
    osmgraph = osm.load_graph(config['<osmfile>'], float(config['--halo']))
    graph_to_gpx(osmgraph, config)


def osmtopickle(config):
    """ Load an OSM file and save the results as a pickle for future use"""
    osmgraph = osm.load_graph(config['<osmfile>'], float(config['--halo']))
    if config['<picklefile>']:
        waysdb.store_graph(osmgraph, config['<picklefile>'])


def pickletogpx(config):
    """ Perform an ACO search over an existing graph to generate a gpx track"""
    osmgraph = waysdb.load_graph(config['<picklefile>'])
    graph_to_gpx(osmgraph, config)


if __name__ == '__main__':
    from docopt import docopt
    config = docopt(__doc__, version="Cycling Ants "+__version__)
    if config['osm']:
        osmtogpx(config)
    elif config['pickle']:
        pickletogpx(config)
    elif config['makepickle']:
        osmtopickle(config)
