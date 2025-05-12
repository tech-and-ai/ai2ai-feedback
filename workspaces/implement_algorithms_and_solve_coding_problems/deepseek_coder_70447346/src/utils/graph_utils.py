# File content goes here
...
# graph_utils.py

def add_edge(graph, u, v):
    if v in graph[u]:
        print('Edge would create a cycle.')
    else:
        graph[u].append(v)


def detect_cycle_util(v, visited, recStack, graph):
    visited[v] = True
    recStack[v] = True

    for neighbour in graph[v]:
        if not visited[neighbour]:
            if detect_cycle_util(neighbour, visited, recStack, graph):
                return True
        elif recStack[neighbour]:
            return True

    recStack[v] = False
    return False


def detect_cycle(graph):
    visited = {node: False for node in graph}
    recStack = {node: False for node in graph}

    for node in graph:
        if not visited[node]:
            if detect_cycle_util(node, visited, recStack, graph):
                return True
    return False


def visualize_graph(graph):
    import matplotlib.pyplot as plt
    from IPython.display import display
    import networkx as nx

    G = nx.DiGraph()

    for node in graph:
        G.add_node(node)
        for neighbour in graph[node]:
            G.add_edge(node, neighbour)

    pos = nx.spring_layout(G)
    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=12, font_weight='bold', arrowstyle='-|>', arrowsize=20)
    plt.title('Dependency Graph')
    display(plt.show())
