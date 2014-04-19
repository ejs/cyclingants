#! /usr/bin/python3
"""
    Usage: osm.py <inputfile>
"""
from collections import Counter
from math import acos, sin, cos, radians
import xml.sax as sax
from xml.sax.handler import ContentHandler

from sizing import total_size
from graph import Graph


def travelable_route(way, tags):
    # TODO: look at expanding these checks
    if tags.get('visible', 'true') == 'false':
        return False
    if tags.get('highway') in ('trunk', 'trunk_link', 'primary', 'primary_link', 'secondary',  'secondary_link', 'tertiary', 'tertiary_link', 'unclassified', 'road', 'cycleway'):
        return True
    if tags.get('cycleway'):
        return True
    return False


def distance_between(alat, alon, blat, blon):
    alat, alon = radians(90-alat), radians(alon)
    blat, blon = radians(90-blat), radians(blon)
    return 6373*acos(sin(alat)*sin(blat)*cos(alon-blon) + cos(alat)*cos(blat))


class Node:
    __slots__ = ["lat", "lon", "interest", "nid", "rest", "way"]

    def __init__(self, lat, lon, nid):
        self.lat = float(lat)
        self.lon = float(lon)
        self.interest = 0
        self.rest = False
        self.nid = int(nid)
        self.way = False

    def apply_tags(self, tags):
        # TODO: refine these more
        if any(t in tags for t in ('historic', 'leisure', 'natural', 'tourism', 'amenity', 'sport')):
            self.interest = 1
        elif tags.get('building') in ('hotel', 'cathedral', 'chapel', 'church', 'university'):
            self.interest = 1
        if (tags.get('building') == 'hotel' or
                tags.get('tourism') in ('alpine_hut', 'camp_site', 'chalet', 'guest_house', 'hostel', 'hotel', 'motel', 'wilderness_hut')):
            self.rest = True
        self.way = travelable_route(None, tags)

    def cost_to(self, next_node):
        if next_node:
            return distance_between(self.lat, self.lon, next_node.lat, next_node.lon)
        else:
            return None


class RouteIntersection:
    intersection = True
    cost_out = 0
    cost_back = 0

    def __init__(self, node):
        self.start = self.stop = self.position = node.lat, node.lon
        self.interest = node.interest
        self.nid = int(node.nid)
        self.rest = node.rest

    def __str__(self):
        return "Intersection {} ({} to {}) cost {}, interest {}".format(self.nid, self.start, self.stop, self.cost_out, self.interest)


class RouteEdge:
    intersection = False

    def __init__(self, nodes):
        self.start = nodes[0].lat, nodes[0].lon
        self.stop = nodes[-1].lat, nodes[-1].lon
        self.cost_out = sum(n1.cost_to(n2) for n1, n2 in zip(nodes, nodes[1:]))
        self.cost_back = sum(n2.cost_to(n1) for n1, n2 in zip(nodes, nodes[1:]))
        self.interest = sum(n.interest for n in nodes[1:-1])
        self.nid = [int(n.nid) for n in nodes[1:-1]]
        self.contains = [int(n.nid) for n in nodes[1:-1]]
        self.rest = any(n.rest for n in nodes[1:-1])

    def __str__(self):
        return "Route Edge {} ({} to {}) cost {}, interest {}".format(self.nid, self.start, self.stop, self.cost_out, self.interest)


class OSMHandler(ContentHandler):
    def __init__(self):
        self.node = None
        self.way = None
        self.ways = []
        self.nodes = {}
        self.tags = {}
        self.nds = []
        self.flag = True
        self.blacklist = {'created_by', 'source'}
        self.graph = Graph()

    def startElement(self, name, attributes):
        if name == 'node':
            self.node = (int(attributes['id']), Node(attributes['lat'], attributes['lon'], attributes['id']))
            self.tags = {}
        elif name == 'tag':
            if attributes['k'] not in self.blacklist:
                self.tags[attributes['k']] = attributes['v']
        elif name =='way':
            self.way = {'id':int(attributes['id'])}
            self.nds = []
            self.tags = {}
        elif name == 'nd':
            self.nds.append(int(attributes['ref']))

    def endElement(self, name):
        if name == 'node':
            self.node[1].apply_tags(self.tags)
            if self.tags.get('visible', 'true') != 'false':
                self.nodes[int(self.node[0])] = self.node[1]
            self.node = None
            self.tags = {}
        elif name == 'way':
            self.way['nodes'] = self.nds
            self.way['tags'] = self.tags
            if travelable_route(self.way, self.tags):
                self.ways.append(self.way)
            self.nds = []
            self.tags = {}
            self.way = None

    def endDocument(self):
        self.way_nodes = Counter(n for way in self.ways for n in set(way['nodes']))
        intersections = set(node for node, count in self.way_nodes.items() if count > 1)
        for n in intersections:
            node = RouteIntersection(self.nodes[n])
            self.graph.set_node(n, node)
        for way in self.ways:
            for a, edge, b in nodes_to_edges(intersections, (self.nodes[nd] for nd in way['nodes'])):
                self.graph.add_edge(a, b, RouteEdge(edge))


def nodes_to_edges(intersections, nodes):
    previous, edge = None, []
    for point in nodes:
        edge.append(point)
        if point.nid in intersections:
            if previous:
                yield previous, edge, point.nid
            previous, edge = point.nid, [point]


def load_graph(filename):
    with open(filename) as source:
        osmhandler = OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse(source)
        graph = osmhandler.graph
        return graph


if __name__ == '__main__':
    from docopt import docopt
    arguments = docopt(__doc__, version="osm data analyser")
    osmhandler = OSMHandler()
    parser = sax.make_parser()
    parser.setContentHandler(osmhandler)
    parser.parse(arguments['<inputfile>'])
    print("Node size {0:,d}kb".format(total_size(osmhandler.nodes)//1024))
    print("Way size {0:,d}kb".format(total_size(osmhandler.ways)//1024))
    print("Graph size {0:,d}".format(total_size(osmhandler.graph)))
    print("Rest points", sum(1 for n in osmhandler.nodes.values() if n.rest)) # 38 for all of south yorkshire seems far too low
    print("Intersting points", sum(1 for n in osmhandler.nodes.values() if n.interest)) # 38 for all of south yorkshire seems far too low
    print("Total waypoints", len(osmhandler.way_nodes))
    print("Total nodes", len(osmhandler.nodes))
    print("Total ways", len(osmhandler.ways))
    print("Total graph nodes", len(osmhandler.graph))
    print(osmhandler.graph)
