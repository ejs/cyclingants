#! /usr/bin/python3
"""
    Usage: osm.py <inputfile> [<outputfile>]
"""
from collections import Counter
import itertools
from math import hypot, acos, sin, cos, radians
import xml.sax as sax
from xml.sax.handler import ContentHandler

from sizing import total_size


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

    def cost_to(self, lat, lon):
        return distance_between(self.position[0], self.position[1], lat, lon)

    def cost_from(self, lat, lon):
        return distance_between(self.position[0], self.position[1], lat, lon)


class RouteEdge:
    intersection = False

    def __init__(self, nodes):
        self.start = nodes[0].lat, nodes[0].lon
        self.stop = nodes[-1].lat, nodes[-1].lon
        self.cost_out = sum(n1.cost_to(n2) for n1, n2 in zip(nodes, nodes[1:]))
        self.cost_back = sum(n2.cost_to(n1) for n1, n2 in zip(nodes, nodes[1:]))
        self.interest = sum(n.interest for n in nodes)
        self.nid = [int(n.nid) for n in nodes]
        self.contains = [int(n.nid) for n in nodes]
        self.rest = any(n.rest for n in nodes)

    def __str__(self):
        return "Route Edge {} ({} to {}) cost {}, interest {}".format(self.nid, self.start, self.stop, self.cost_out, self.interest)

    def cost_to(self, lat, lon):
        return distance_between(self.start[0], self.start[1], lat, lon)

    def cost_from(self, lat, lon):
        return distance_between(self.stop[0], self.stop[1], lat, lon)



class OSMHandler(ContentHandler):
    def __init__(self):
        self.node = None
        self.way = None
        self.ways = []
        # TODO: store nodes in simple db to simplify access. If haloing with a square then SQLite should be fine
        self.nodes = {}
        self.tags = {}
        self.nds = []
        self.flag = True
        self.blacklist = {'created_by', 'source'}

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
        count = itertools.count(1)
        for way in self.ways:
            way['nodes'] = list(nodes_to_intersections_and_routes(intersections, (self.nodes[nd] for nd in way['nodes'])))


def nodes_to_intersections_and_routes(intersections, nodes):
    count = itertools.count(1)
    for intersection, clump in itertools.groupby(nodes, key=lambda n: n.nid in intersections and next(count)):
        if intersection:
            yield RouteIntersection(list(clump)[0])
        else:
            yield RouteEdge(list(clump))


def load_file(filename):
    with open(filename) as source:
        osmhandler = OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse(source)
        return osmhandler.ways


if __name__ == '__main__':
    from docopt import docopt
    arguments = docopt(__doc__, version="osm data loader 0.1")
    osmhandler = OSMHandler()
    parser = sax.make_parser()
    parser.setContentHandler(osmhandler)
    parser.parse(arguments['<inputfile>'])
    print("Node size {0:,d}kb".format(total_size(osmhandler.nodes)//1024))
    print("Way size {0:,d}kb".format(total_size(osmhandler.ways)//1024))
    print("Most interesting block", max(sum(r.interest for r in w['nodes']) for w in osmhandler.ways))
    print("Rest points", sum(1 for n in osmhandler.nodes.values() if n.rest)) # 38 for all of south yorkshire seems far too low
    print("Intersting points", sum(1 for n in osmhandler.nodes.values() if n.interest)) # 38 for all of south yorkshire seems far too low
    print("Surprsing waypoints", sum(1 for n in osmhandler.nodes.values() if not n.way and n.nid in osmhandler.way_nodes))
    print("Total waypoints", len(osmhandler.way_nodes))
    print("Total nodes", len(osmhandler.nodes))
    print("Total ways", len(osmhandler.ways))
    if arguments['<outputfile>' ]:
        import waysdb
        waysdb.store_file(osmhandler.ways, arguments['<outputfile>'])
