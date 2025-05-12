# File content goes here
...
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt

def add_edge(graph, u, v):
    graph[u].append(v)

def has_cycle_util(node, visited, recStack, graph):
    if node not in visited:
        visited.add(node)
        recStack.add(node)
        for neighbour in graph[node]:
            if (neighbour not in visited or neighbour in recStack) and has_cycle_util(neighbour, visited, recStack, graph):
                return True
        recStack.remove(node)
    return False

def has_cycle(graph):
    visited = set()
    recStack = set()
    for node in list(graph):
        if not node in visited:
            if has_cycle_util(node, visited, recStack, graph):
                return True
    return False

def detect_cycles(graph):
    cycles = []
    visited = set()
    stack = []
    for node in list(graph):
        if node not in visited:
            dfs(node, visited, stack, graph)
            while stack:
                current = stack.pop()
                cycle = []
                while current != node and current is not None:
                    cycle.append(current)
                    current = stack[-1] if len(stack) > 0 else None
                if current: # If it's a SCC, we have found a cycle
                    cycles.append(cycle[::-1])
    return cycles

def dfs(node, visited, stack, graph):
    if node not in visited:
        visited.add(node)
        stack.append(node)
        for neighbour in graph[node]:
            dfs(neighbour, visited, stack, graph)

def visualize_graph(graph):
    G = nx.DiGraph()
    for node, neighbours in graph.items():
        G.add_node(node)
        for neighbour in neighbours:
            G.add_edge(node, neighbour)
    pos = nx.spring_layout(G)  # positions for all nodes
    plt.figure(figsize=(10,8))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', font_weight='bold', node_size=700, font_size=10)
    plt.show()
