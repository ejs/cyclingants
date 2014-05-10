#! /usr/bin/python3
"""
    Usage: osm.py <inputfile>
"""
from collections import Counter
from math import acos, sin, cos, radians
from time import time
import sqlite3
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

    def __init__(self, lat, lon, nid, interest=0, rest=False):
        self.lat = float(lat)
        self.lon = float(lon)
        self.interest = interest
        self.rest = rest
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


class NodeDB:
    def __init__(self, target):
        self.db = sqlite3.connect(target)
        dbc = self.db.cursor()
        dbc.execute("""CREATE TABLE nodes (
            id INTEGER PRIMARY KEY,
            lat REAL,
            lon REAL,
            interest INTEGER DEFAULT 0,
            rest INTEGER DEFAULT 0,
            is_way INTEGER DEFAULT 0,
            closest_way INTEGER DEFAULT 0)""")
        self.db.commit()

    def create_node(self, nodeid, node):
        dbc = self.db.cursor()
        dbc.execute('INSERT INTO nodes VALUES (?, ?, ?, ?, ?, 0, 0)',
                        (node.nid, node.lat, node.lon, node.interest, node.rest))
        self.db.commit()

    def get_node(self, nodeid):
        dbc = self.db.cursor()
        dbc.execute('SELECT lat, lon, id, interest, rest FROM nodes WHERE id=?', (nodeid, ))
        return Node(*dbc.fetchone())

    def mark_as_route(self, nodeid):
        dbc = self.db.cursor()
        dbc.execute('SELECT is_way FROM nodes WHERE id=?', (nodeid, ))
        newval = dbc.fetchone()[0] +1
        dbc.execute('UPDATE nodes SET is_way=? WHERE id=?', (newval, nodeid))
        self.db.commit()

    def load_intersections(self):
        dbc = self.db.cursor()
        for nid in dbc.execute('SELECT id FROM nodes WHERE is_way>1'):
            yield nid[0]


class RouteIntersection:
    def __init__(self, node):
        self.start = self.stop = self.position = node.lat, node.lon
        self.interest = node.interest
        self.nid = int(node.nid)
        self.rest = node.rest

    def __str__(self):
        return "Intersection {} ({} to {}) cost {}, interest {}".format(self.nid, self.start, self.stop, self.cost_out, self.interest)


class RouteEdge:
    def __init__(self, nodes):
        self.cost_out = sum(n1.cost_to(n2) for n1, n2 in zip(nodes, nodes[1:]))
        self.interest = sum(n.interest for n in nodes[1:-1])
        self.nid = [int(n.nid) for n in nodes[1:-1]]
        self.rest = any(n.rest for n in nodes[1:-1])

    def __str__(self):
        return "Route Edge {}, cost {}, interest {}".format(self.nid, self.cost_out, self.interest)


class OSMHandler(ContentHandler):
    def __init__(self):
        self.node = None
        self.way = None
        self.ways = []
        self.tags = {}
        self.nds = []
        self.flag = True
        self.graph = Graph()
        self.db = NodeDB(':memory:')
        self.count = 0
        self.start = time()

    def startElement(self, name, attributes):
        if name == 'node':
            self.node = (int(attributes['id']), Node(attributes['lat'], attributes['lon'], attributes['id']))
            self.tags = {}
        elif name == 'tag':
            self.tags[attributes['k']] = attributes['v']
        elif name =='way':
            self.way = {'id':int(attributes['id'])}
            self.nds = []
            self.tags = {}
        elif name == 'nd':
            self.nds.append(int(attributes['ref']))

    def endElement(self, name):
        steps = 100000
        if name == 'node':
            self.node[1].apply_tags(self.tags)
            if self.tags.get('visible', 'true') != 'false':
                self.db.create_node(*self.node)
                self.count += 1
                if not self.count%steps:
                    print(self.count, 'nodes', time()-self.start)
            self.node = None
            self.tags = {}
        elif name == 'way':
            self.way['nodes'] = self.nds
            self.way['tags'] = self.tags
            if travelable_route(self.way, self.tags):
                for node in set(self.nds):
                    self.db.mark_as_route(node)
                self.ways.append(self.way)
                self.count += 1
                if not self.count%steps:
                    print(self.count, 'ways', time()-self.start)
            self.nds = []
            self.tags = {}
            self.way = None

    def endDocument(self):
        intersections = set(self.db.load_intersections())
        for n in intersections:
            self.graph.set_node(n, RouteIntersection(self.db.get_node(n)))
        for way in self.ways:
            for a, edge, b in nodes_to_edges(intersections, map(self.db.get_node, way['nodes'])):
                self.graph.add_edge(a, b, RouteEdge(edge))
        self.graph.trim()


def nodes_to_edges(intersections, nodes):
    previous, edge = None, []
    for point in nodes:
        edge.append(point)
        if point.nid in intersections:
            if previous:
                yield previous, edge, point.nid
                yield point.nid, edge[::-1], previous
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
    print("Way size {0:,d}kb".format(total_size(osmhandler.ways)//1024))
    print("Total ways", len(osmhandler.ways))
    print("Total graph nodes", len(osmhandler.graph))
    print("Connected components", osmhandler.graph.connected_components())
    print(osmhandler.graph)
