# test_graph_utils.py
import unittest
from src.utils.graph_utils import add_edge, detect_cycle, visualize_graph

def create_graph():
    return {'A': ['B'], 'B': ['C'], 'C': []}

class TestGraphUtils(unittest.TestCase):
    def test_add_edge_no_cycle(self):
        graph = create_graph()
        add_edge(graph, 'A', 'D')
        self.assertEqual(len(graph['D']), 0)

    def test_add_edge_cycle(self):
        graph = create_graph()
        with self.assertRaises(Exception) as context:
            add_edge(graph, 'C', 'A')
        self.assertTrue('Edge would create a cycle.' in str(context.exception))

    def test_detect_cycle(self):
        graph = create_graph()
        graph['D'] = ['B']
        self.assertTrue(detect_cycle(graph))

    def test_visualize_graph(self):
        graph = create_graph()
        visualize_graph(graph)
