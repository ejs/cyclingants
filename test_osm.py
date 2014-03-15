#! /usr/bin/python3
from collections import Counter
import osm
import unittest
import xml.sax as sax

from sizing import total_size


class TestLoading(unittest.TestCase):
    def test_loading(self):
        osmhandler = osm.OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse('south-yorkshire-latest.osm')
        res = osmhandler.nodes, osmhandler.ways, osmhandler.graph
        self.assertEqual(len(res[0]), 1076738)
        self.assertEqual(len(res[1]), 10164)
        print("Node size", total_size(res[0]))
        print("Way size", total_size(res[1][:100]))
        print("Graph size", total_size(res[2]))
        print(Counter(len(b) for b in res[2].values()))
        print(max(sum(r.interest for r in w['nodes']) for w in res[1]))

    def test_loading_with_geograhic_restriction(self):
        pass



if __name__ == '__main__':
    unittest.main()
