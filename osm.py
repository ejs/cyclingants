#! /usr/bin/python3
from collections import defaultdict, Counter
import itertools
from math import hypot
import xml.sax as sax
from xml.sax.handler import ContentHandler

from sizing import total_size


def travelable_route(way, tags):
    if tags.get('visible', 'true') == 'false':
        return False
    if tags.get('highway') in ('trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'road', 'cycleway'):
        return True
    if tags.get('cycleway'):
        return True
    return False


class Node:
    __slots__ = ["lat", "lon", "interest", "nid", "rest"]

    def __init__(self, lat, lon, nid):
        self.lat = float(lat)
        self.lon = float(lon)
        self.interest = 0
        self.rest = False
        self.nid = int(nid)

    def apply_tags(self, tags):
        # TODO: refine these more
        if any(t in tags for t in ('historic', 'leisure', 'natural', 'tourism', 'amenity', 'sport')):
            self.interest = 1
        elif tags.get('building') in ('hotel', 'cathedral', 'chapel', 'church', 'university'):
            self.interest = 1
        if (tags.get('building') == 'Hotel' or
                tags.get('tourism') in ('alpine_hut', 'camp_site', 'chalet', 'guest_house', 'hostel', 'hotel', 'motel', 'wilderness_hut')):
            self.rest = True

    def cost_to(self, next_node):
        if next_node:
            return hypot(self.lat-next_node.lat, self.lon-next_node.lon)
        else:
            return None


class RouteSection:
    def __init__(self, info):
        self.intersection, nodes = info
        self.intersection = bool(self.intersection)
        nodes = list(nodes)
        self.start = nodes[0].lat, nodes[0].lon
        self.stop = nodes[-1].lat, nodes[-1].lon
        self.cost_out = sum(n1.cost_to(n2) for n1, n2 in zip(nodes, nodes[1:]))
        self.cost_back = sum(n2.cost_to(n1) for n1, n2 in zip(nodes[1:], nodes)) # TODO: double check this
        self.interest = sum(n.interest for n in nodes)
        if self.intersection:
            self.nid = int(nodes[0].nid)
        else:
            self.nid = [int(n.nid) for n in nodes]
        self.rest = any(n.rest for n in nodes)

    def __str__(self):
        return "{} ({} to {}) cost {}, interest {}".format(self.nid, self.start, self.stop, self.cost_out, self.interest)

    def __repr__(self):
        return "Route Section <{} ({} to {}) cost {}, interest {}>".format(self.nid, self.start, self.stop, self.cost_out, self.interest)

    def cost_to(self, lat, lon):
        return hypot(self.start[0]-lat, self.start[1]-lon)

    def cost_from(self, lat, lon):
        return hypot(self.stop[0]-lat, self.stop[1]-lon)


class ACOEdge:
    __slots__ = ["next_id", "cost", "interest", "pheremones", "rest"]

    def __init__(self, nid, cost, interest, rest):
        self.next_id = nid
        self.cost = cost
        self.interest = interest
        self.pheremones = 0
        self.rest = rest


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
        simplify_ways(self.ways, self.nodes)
        self.graph = clean_graph(ways_to_graph(self.ways))


def clean_graph(graph):
    stats = Counter(len(b) for b in graph.values())
    # TODO: look at spotting/removing closed loops
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


def simplify_ways(ways, nodes):
    node_use = Counter(n for way in ways for n in set(way['nodes']))
    intersections = set(node for node, count in node_use.items() if count > 1)
    count = itertools.count(1)
    for way in ways:
        nds = (nodes[nd] for nd in way['nodes'])
        grouped_nodes = itertools.groupby(nds, key=lambda n: n.nid in intersections and next(count))
        combined_nodes = map(RouteSection, grouped_nodes)
        way['nodes'] = list(combined_nodes)


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


def load_file(filename):
    with open(filename) as source:
        osmhandler = OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse(source)
        return osmhandler.graph


if __name__ == '__main__':
    osmhandler = OSMHandler()
    parser = sax.make_parser()
    parser.setContentHandler(osmhandler)
    parser.parse('south-yorkshire-latest.osm')
    res = osmhandler.nodes, osmhandler.ways, osmhandler.graph
    print("Node size", total_size(res[0]))
    print("Way size", total_size(res[1][:100]))
    print("Graph size", total_size(res[2]))
    print("Graph stats", Counter(len(b) for b in res[2].values()))
    print("Most interesting block", max(sum(r.interest for r in w['nodes']) for w in res[1]))
    print("Rest points ", sum(1 for r in res[1] for n in r['nodes'] if n.rest))
    print("Input rest points", sum(1 for r in res[0].values() if r.rest)) # 38 for all of south yorkshire seems far too low
