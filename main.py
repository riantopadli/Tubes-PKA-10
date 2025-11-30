class Graph:
    def __init__(self):
        # Adjacency list: node -> list of (tetangga, bobot)
        self.nodes = set()
        self.edges = {}
        self.coordinates = {}  # opsional, untuk heuristic A*

    def add_node(self, node, coord=None):
        self.nodes.add(node)
        if node not in self.edges:
            self.edges[node] = []
        if coord is not None:
            self.coordinates[node] = coord  # (x, y) tuple

    def add_edge(self, from_node, to_node, weight):
        self.add_node(from_node)
        self.add_node(to_node)
        self.edges[from_node].append((to_node, weight))
        self.edges[to_node].append((from_node, weight))  # Jika graf dua arah

    def dijkstra(self, start, end):
        import heapq
        queue = []
        heapq.heappush(queue, (0, start, [start]))
        visited = set()
        while queue:
            (cost, node, path) = heapq.heappop(queue)
            if node == end:
                return cost, path
            if node in visited:
                continue
            visited.add(node)
            for neighbor, weight in self.edges.get(node, []):
                if neighbor not in visited:
                    heapq.heappush(queue, (cost+weight, neighbor, path+[neighbor]))
        return float('inf'), []

    def heuristic(self, node, goal):
        # jika punya koordinat, gunakan Euclidean distance
        c1 = self.coordinates.get(node)
        c2 = self.coordinates.get(goal)
        if c1 and c2:
            return ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
        return 0  # fallback heuristic

    def astar(self, start, end):
        import heapq
        queue = []
        heapq.heappush(queue, (0 + self.heuristic(start,end), 0, start, [start]))
        visited = set()
        while queue:
            (est_total, cost, node, path) = heapq.heappop(queue)
            if node == end:
                return cost, path
            if node in visited:
                continue
            visited.add(node)
            for neighbor, weight in self.edges.get(node, []):
                if neighbor not in visited:
                    g = cost + weight
                    h = self.heuristic(neighbor, end)
                    heapq.heappush(queue, (g + h, g, neighbor, path + [neighbor]))
        return float('inf'), []

    def __str__(self):
        result = ''
        for node in self.edges:
            result += f'{node}: {self.edges[node]}\n'
        return result

# Data contoh
# Lokasi dengan koordinat sederhana agar A* tetap jalan
# Depot, Pom1-4, S1-6
location_coords = {
    "Depot": (0,0),
    "S1": (2,2),
    "S2": (5,2),
    "S3": (2,5),
    "S4": (8,2),
    "S5": (4,7),
    "S6": (7,7),
    "Pom1": (6,0),
    "Pom2": (0,7),
    "Pom3": (10,0),
    "Pom4": (10,8)
}

roads = [
    ("Depot", "S1", 5),
    ("S1", "S2", 3),
    ("S1", "S3", 2),
    ("S2", "Pom1", 4),
    ("S2", "S4", 2),
    ("S3", "Pom2", 6),
    ("S3", "S5", 2),
    ("S4", "Pom3", 5),
    ("S5", "S6", 3),
    ("S6", "Pom4", 4)
]

def create_example_graph():
    graph = Graph()
    # add nodes with coordinates
    for loc, coord in location_coords.items():
        graph.add_node(loc, coord)
    # add edges
    for from_node, to_node, weight in roads:
        graph.add_edge(from_node, to_node, weight)
    return graph

if __name__ == "__main__":
    g = create_example_graph()
    print("Graf kota dan pom bensin:")
    print(g)

    depot = "Depot"
    poms = ["Pom1", "Pom2", "Pom3", "Pom4"]
    print("\n=== Dijkstra ===")
    for pom in poms:
        cost, path = g.dijkstra(depot, pom)
        print(f"Rute terpendek Dijkstra dari {depot} ke {pom}: {path}, jarak: {cost}")
    print("\n=== A* (A Star) ===")
    for pom in poms:
        cost, path = g.astar(depot, pom)
        print(f"Rute terpendek A* dari {depot} ke {pom}: {path}, jarak: {cost}")
