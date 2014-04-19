#! /usr/bin/python3
import unittest
import graph


class TestGraph(unittest.TestCase):
    def test_empty_graph(self):
        g = graph.Graph()
        self.assertEqual(len(g), 0)

    def test_add_node_to_graph(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        self.assertEqual(len(g), 1)
        self.assertEqual(g.get_node(1), (2, 3))

    def test_add_edge_between_nodes(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.add_edge(1, 4, (7, 8))
        self.assertEqual(len(g.get_edges(1)), 1)
        self.assertEqual(len(g.get_edges(1, 4)), 1)
        self.assertEqual(g.get_edges(1, 4)[0], (7, 8))

    def test_edges_are_directional(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.add_edge(1, 4, (7, 8))
        self.assertEqual(len(g.get_edges(4)), 0)

    def test_add_two_edges(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.set_node(7, (8, 9))
        g.add_edge(1, 4, (10, 11))
        g.add_edge(1, 7, (12, 13))
        self.assertEqual(len(g.get_edges(1)), 2)
        self.assertEqual(len(g.get_edges(1, 4)), 1)
        self.assertEqual(g.get_edges(1, 4)[0], (10, 11))

    def test_add_two_edge_between_the_same_nodes(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.add_edge(1, 4, (7, 8))
        g.add_edge(1, 4, (9, 10))
        self.assertEqual(len(g.get_edges(1)), 2)
        self.assertEqual(len(g.get_edges(1, 4)), 2)
        self.assertIn((7, 8), g.get_edges(1, 4))
        self.assertIn((9, 10), g.get_edges(1, 4))

    def test_remove_node(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.del_node(1)
        self.assertEqual(len(g), 0)

    def test_remove_node_with_link_out(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.add_edge(1, 4, (10, 11))
        g.del_node(1)
        self.assertEqual(len(g), 1)

    def test_remove_node_with_link_in(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.add_edge(1, 4, (10, 11))
        g.del_node(4)
        self.assertEqual(len(g), 1)
        self.assertEqual(len(g.get_edges(1)), 0)

    def test_clean_removes_node_without_links(self):
        g = graph.Graph()
        g.set_node(1, (2, 3))
        g.set_node(4, (5, 6))
        g.set_node(7, (8, 9))
        g.add_edge(1, 4, (10, 11))
        g.clean()
        self.assertEqual(len(g), 2)

    def build_complex_graph(self):
        g = graph.Graph()
        g.set_node("n1", (0, 1))
        g.set_node("n2", (0, 2))
        g.set_node("n3", (0, 3))
        g.set_node("n4", (0, 4))
        g.set_node("n5", (0, 5))
        g.set_node("n6", (0, 6))
        g.set_node("n7", (0, 7))
        g.set_node("n8", (0, 8))
        g.set_node("n9", (0, 9))
        g.set_node("n10", (1, 1))
        g.set_node("n11", (1, 2))
        g.set_node("n12", (1, 3))
        g.set_node("n13", (1, 4))
        g.add_edge("n1", "n2", (1, 2))
        g.add_edge("n2", "n1", (2, 1))
        g.add_edge("n1", "n4", (1, 4))
        g.add_edge("n4", "n1", (4, 1))
        g.add_edge("n1", "n5", (1, 5))
        g.add_edge("n5", "n1", (5, 1))
        g.add_edge("n1", "n8", (1, 8))
        g.add_edge("n8", "n1", (8, 1))
        g.add_edge("n1", "n9", (1, 9))
        g.add_edge("n9", "n1", (9, 1))
        g.add_edge("n2", "n3", (2, 3))
        g.add_edge("n3", "n2", (3, 2))
        g.add_edge("n2", "n5", (2, 5))
        g.add_edge("n5", "n2", (5, 2))
        g.add_edge("n2", "n8", (2, 8))
        g.add_edge("n8", "n2", (8, 2))
        g.add_edge("n2", "n10", (2, 10))
        g.add_edge("n10", "n2", (10, 2))
        g.add_edge("n3", "n5", (2, 5))
        g.add_edge("n5", "n3", (5, 2))
        g.add_edge("n3", "n6", (2, 6))
        g.add_edge("n6", "n3", (6, 2))
        g.add_edge("n4", "n5", (4, 5))
        g.add_edge("n5", "n4", (5, 4))
        g.add_edge("n4", "n6", (4, 6))
        g.add_edge("n6", "n4", (6, 4))
        g.add_edge("n6", "n7", (6, 7))
        g.add_edge("n7", "n6", (7, 6))
        g.add_edge("n6", "n7", (-6, 7))
        g.add_edge("n7", "n6", (7, -6))
        g.add_edge("n10", "n11", (10, 11))
        g.add_edge("n11", "n10", (11, 10))
        g.add_edge("n10", "n12", (10, 12))
        g.add_edge("n12", "n10", (12, 10))
        return g

    def test_clean_complex_graph(self):
        g = self.build_complex_graph()
        g.clean()
        self.assertEqual(len(g), 12)

    def test_trim_graph(self):
        g = self.build_complex_graph()
        g.trim()
        self.assertEqual(len(g), 8)

    def test_compact_graph(self):
        g = self.build_complex_graph()
        g.compact()
        self.assertEqual(len(g), 7)

    def test_most_connected_nodes(self):
        g = self.build_complex_graph()
        self.assertEqual(g.find_most_connected_nodes(), ["n1", "n2"])

    def test_tranform_ids(self):
        g = self.build_complex_graph()
        gt = g.transform(t_id=lambda a: "-"+a)
        self.assertEqual(len(g), len(gt))
        self.assertEqual(g.get_node("n1"), gt.get_node("-n1"))
        self.assertEqual(g.get_edges("n1", "n2"), gt.get_edges("-n1", "-n2"))

    def test_tranform_nodes(self):
        g = self.build_complex_graph()
        gt = g.transform(t_node=lambda a:list(reversed(a)))
        self.assertEqual(len(g), len(gt))
        self.assertEqual(gt.get_node("n1"), [1, 0])

    def test_tranform_edge(self):
        g = self.build_complex_graph()
        gt = g.transform(t_edge=lambda a:list(reversed(a)))
        self.assertEqual(len(g), len(gt))
        self.assertEqual(gt.get_edges("n10", "n12")[0], [12, 10])


if __name__ == '__main__':
    unittest.main()
