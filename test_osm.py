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


if __name__ == '__main__':
    unittest.main()
