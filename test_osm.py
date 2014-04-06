#! /usr/bin/python3
import unittest
import xml.sax as sax

import osm


@unittest.skip("long test")
class TestFullRun(unittest.TestCase):
    def test_loading(self):
        osmhandler = osm.OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse('isle-of-wight-latest.osm')
        self.assertEqual(len(osmhandler.nodes), 188334)
        self.assertEqual(len(osmhandler.ways), 1820)


class TestRoutAnalysis(unittest.TestCase):
    def test_no_tags(self):
        tags = {}
        self.assertEqual(osm.travelable_route(None, tags), False);

    def test_match_trunk_road(self):
        tags = {'highway':'trunk'}
        self.assertEqual(osm.travelable_route(None, tags), True);

    def test_dont_match_invisible(self):
        tags = {'highway':'trunk', 'visible':'false'}
        self.assertEqual(osm.travelable_route(None, tags), False);

    def test_do_match_explicitly_visible(self):
        tags = {'highway':'trunk', 'visible':'true'}
        self.assertEqual(osm.travelable_route(None, tags), True);


class TestNode(unittest.TestCase):
    def test_node_initialisation(self):
        node = osm.Node(1, 2, 3)
        self.assertEqual(node.lat, 1)
        self.assertEqual(node.lon, 2)
        self.assertEqual(node.interest, 0)
        self.assertEqual(node.rest, False)
        self.assertEqual(node.nid, 3)
        self.assertEqual(node.way, False)

    def test_node_initialisation_corrects_id(self):
        node = osm.Node(1, 2, "3")
        self.assertEqual(node.nid, 3)

    def test_node_handles_addition_of_no_tags(self):
        node = osm.Node(1, 2, 3)
        node.apply_tags({})
        self.assertEqual(node.interest, 0)
        self.assertEqual(node.rest, False)
        self.assertEqual(node.way, False)

    def test_node_handles_being_interesting(self):
        node = osm.Node(1, 2, 3)
        node.apply_tags({'historic':'castle'})
        self.assertEqual(node.interest, 1)
        self.assertEqual(node.rest, False)
        self.assertEqual(node.way, False)

    def test_node_handles_being_very_interesting(self):
        node = osm.Node(1, 2, 3)
        node.apply_tags({'historic':'castle', 'building':'chapel'})
        self.assertEqual(node.interest, 1)
        self.assertEqual(node.rest, False)
        self.assertEqual(node.way, False)

    def test_node_handles_being_a_rest_point(self):
        node = osm.Node(1, 2, 3)
        node.apply_tags({'building':'hotel'})
        self.assertEqual(node.interest, 1)
        self.assertEqual(node.rest, True)
        self.assertEqual(node.way, False)

    def test_node_calculates_costs_correctly(self):
        node_a = osm.Node(1, 2, 3)
        node_b = osm.Node(2, 1, 4)
        self.assertEqual(int(node_a.cost_to(node_b)), 157)
        self.assertEqual(int(node_b.cost_to(node_a)), 157)




if __name__ == '__main__':
    unittest.main()
