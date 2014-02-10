from collections import defaultdict
import xml.sax as sax
from xml.sax.handler import ContentHandler

def clean_irrelivant(d):
    d.pop('uid', None)
    d.pop('version', None)
    d.pop('timestamp', None)
    d.pop('user', None)
    d.pop('changeset', None)


class OSMHandler(ContentHandler):
    def __init__(self):
        self.node = None
        self.way = None
        self.ways = []
        self.nodes = {}
        self.seen = set()
        self.tags = defaultdict(list)
        self.nds = []
        self.flag = True
        self.blacklist = {'created_by', 'source'}
        self.waycount = 0

    def startElement(self, name, attributes):
        if name == 'node':
            self.node = (int(attributes['id']),
                         {'lat':float(attributes['lat']),
                           'lon':float(attributes['lon'])})
            self.tags = defaultdict(list)
        elif name == 'tag':
            if attributes['k'] not in self.blacklist:
                self.tags[attributes['k']] = attributes['v']
        elif name =='way':
            self.way = {'id':int(attributes['id'])}
            self.nds = []
            self.tags = defaultdict(list)
        elif name == 'nd':
            self.nds.append(int(attributes['ref']))
        elif name not in self.seen:
            print(name, dict(attributes))
            self.seen.add(name)

    def endElement(self, name):
        if name == 'node':
            if self.tags:
                self.node[1]['tags'] = self.tags
                self.tags = defaultdict(list)
            else:
                self.tags = None
            self.nodes[self.node[0]] = self.node[1]
            self.node = None
        elif name == 'way':
            self.way['nodes'] = self.nds
            self.way['tags'] = self.tags
            if 'highway' in self.tags:
                self.ways.append(self.way)
                self.waycount += 1
            self.nds = []
            self.tags = defaultdict(list)
            self.way = None

    def endDocument(self):
        print("Total ways", self.waycount)


def load_file(filename):
    with open(filename) as source:
        osmhandler = OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse(source)
        return osmhandler.nodes, osmhandler.ways
