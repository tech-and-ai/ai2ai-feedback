class Graph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, u, v):
        if u not in self.graph:
            self.graph[u] = []
        self.graph[u].append(v)

    def is_cyclic_util(self, v, visited, recStack):
        visited[v] = True
        recStack[v] = True
        for neighbour in self.graph.get(v, []):
            if not visited[neighbour]:
                if self.is_cyclic_util(neighbour, visited, recStack):
                    return True
            elif recStack[neighbour]:
                return True
        recStack[v] = False
        return False

    def is_cyclic(self):
        visited = {node: False for node in self.graph}
        recStack = {node: False for node in self.graph}
        for node in self.graph:
            if not visited[node]:
                if self.is_cyclic_util(node, visited, recStack):
                    return True
        return False

    def visualize(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        G = nx.DiGraph()
        for node in self.graph:
            for neighbour in self.graph[node]:
                G.add_edge(node, neighbour)
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, 
                node_color='lightblue', font_weight='bold', arrows=True)
        plt.show()