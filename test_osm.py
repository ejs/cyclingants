#! /usr/bin/python3
import unittest
import xml.sax as sax

import graph
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
        self.assertEqual(len(osmhandler.graph), 1599)


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


class TestRouteIntersection(unittest.TestCase):
    def test_init(self):
        nd = osm.Node(1, 2, 3)
        ri = osm.RouteIntersection(nd)
        self.assertEqual(ri.position, (1, 2))
        self.assertEqual(ri.position, ri.start)
        self.assertEqual(ri.position, ri.stop)
        self.assertEqual(ri.cost_out, 0)
        self.assertEqual(ri.cost_back, 0)
        self.assertEqual(ri.interest, False)
        self.assertEqual(ri.intersection, True)
        self.assertEqual(ri.nid, 3)
        self.assertEqual(ri.rest, False)


class TestRouteEdge(unittest.TestCase):
    def test_init_with_two_boring_nodes(self):
        nd = osm.Node(1, 2, 3)
        nd2 = osm.Node(2, 1, 4)
        re = osm.RouteEdge([nd, nd2])
        self.assertEqual(re.start, (1, 2))
        self.assertEqual(re.stop, (2, 1))
        self.assertEqual(int(re.cost_out), 157)
        self.assertEqual(int(re.cost_back), 157)
        self.assertEqual(re.interest, 0)
        self.assertEqual(re.intersection, False)
        self.assertEqual(re.nid, [])
        self.assertEqual(re.rest, False)

    def test_init_with_multiple_interesting_nodes(self):
        nd = osm.Node(1, 2, 3)
        nd.interest = 1
        nd2 = osm.Node(2, 1, 4)
        nd2.interest = 1
        nd3 = osm.Node(2, 1, 5)
        nd3.interest = 1
        re = osm.RouteEdge([nd, nd3, nd2])
        self.assertEqual(re.start, (1, 2))
        self.assertEqual(re.stop, (2, 1))
        self.assertEqual(int(re.cost_out), 157)
        self.assertEqual(int(re.cost_back), 157)
        self.assertEqual(re.interest, 1)
        self.assertEqual(re.intersection, False)
        self.assertEqual(re.nid, [5])
        self.assertEqual(re.rest, False)

    def test_init_with_multiple_rest_nodes(self):
        nd = osm.Node(1, 2, 3)
        nd.rest = True
        nd2 = osm.Node(2, 1, 4)
        nd2.rest = True
        nd3 = osm.Node(2, 1, 5)
        nd3.rest = True
        re = osm.RouteEdge([nd, nd3, nd2])
        self.assertEqual(re.start, (1, 2))
        self.assertEqual(re.stop, (2, 1))
        self.assertEqual(int(re.cost_out), 157)
        self.assertEqual(int(re.cost_back), 157)
        self.assertEqual(re.interest, 0)
        self.assertEqual(re.intersection, False)
        self.assertEqual(re.nid, [5])
        self.assertEqual(re.rest, True)


class TestWayToGraph(unittest.TestCase):
    pass


class TestOSMHandler(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
