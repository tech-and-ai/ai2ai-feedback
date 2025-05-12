# File content goes here
...
import unittest
from src.utils.graph_util import add_edge, has_cycle, detect_cycles, visualize_graph
from collections import defaultdict

class TestGraphUtil(unittest.TestCase):
    def setUp(self):
        self.graph = defaultdict(list)

    def test_add_edge_no_cycle(self):
        add_edge(self.graph, 'A', 'B')
        self.assertFalse(has_cycle(self.graph))

    def test_add_edge_creates_cycle(self):
        add_edge(self.graph, 'A', 'B')
        add_edge(self.graph, 'B', 'C')
        add_edge(self.graph, 'C', 'A'  # Creates a cycle)
        self.assertTrue(has_cycle(self.graph))

    def test_detect_cycles(self):
        add_edge(self.graph, 'A', 'B')
        add_edge(self.graph, 'B', 'C')
        add_edge(self.graph, 'C', 'D')
        add_edge(self.graph, 'D', 'A'  # Creates a cycle)
        cycles = detect_cycles(self.graph)
        self.assertEqual(len(cycles), 1)

    def test_visualize_graph(self):
        add_edge(self.graph, 'A', 'B')
        add_edge(self.graph, 'B', 'C')
        visualize_graph(self.graph)

if __name__ == '__main__':
    unittest.main()
