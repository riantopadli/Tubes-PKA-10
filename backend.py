import math
import heapq
import itertools
from itertools import permutations
from typing import Dict, List, Optional, Set, Tuple

# --- KELAS GRAPH & ALGORITMA ---
class Graph:
    def __init__(self, average_speed_kmph: float = 30.0):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, List[Tuple[str, float]]] = {}
        self.coordinates: Dict[str, Tuple[float, float]] = {}
        self.average_speed_kmph = average_speed_kmph

    def add_node(self, node: str, coord: Optional[Tuple[float, float]] = None) -> None:
        self.nodes.add(node)
        if node not in self.edges:
            self.edges[node] = []
        if coord is not None:
            self.coordinates[node] = coord

    def add_edge(self, from_node: str, to_node: str, weight: float) -> None:
        self.add_node(from_node)
        self.add_node(to_node)
        self.edges[from_node].append((to_node, weight))
        self.edges[to_node].append((from_node, weight))

    def dijkstra(self, start: str, end: str) -> Tuple[float, List[str]]:
        queue: List[Tuple[float, str, List[str]]] = []
        heapq.heappush(queue, (0.0, start, [start]))
        visited: Set[str] = set()
        while queue:
            cost, node, path = heapq.heappop(queue)
            if node == end:
                return cost, path
            if node in visited:
                continue
            visited.add(node)
            for neighbor, weight in self.edges.get(node, []):
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
        return float("inf"), []

    def heuristic(self, node: str, goal: str) -> float:
        c1 = self.coordinates.get(node)
        c2 = self.coordinates.get(goal)
        if c1 and c2 and self.average_speed_kmph > 0:
            distance_km = haversine_km(c1, c2)
            return (distance_km / self.average_speed_kmph) * 60.0
        return 0.0

    def astar(self, start: str, end: str) -> Tuple[float, List[str]]:
        queue: List[Tuple[float, float, str, List[str]]] = []
        heapq.heappush(queue, (self.heuristic(start, end), 0.0, start, [start]))
        visited: Set[str] = set()
        while queue:
            est_total, cost, node, path = heapq.heappop(queue)
            if node == end:
                return cost, path
            if node in visited:
                continue
            visited.add(node)
            for neighbor, weight in self.edges.get(node, []):
                if neighbor not in visited:
                    g_cost = cost + weight
                    h_cost = self.heuristic(neighbor, end)
                    heapq.heappush(queue, (g_cost + h_cost, g_cost, neighbor, path + [neighbor]))
        return float("inf"), []

AVERAGE_SPEED_KMPH = 30.0

def haversine_km(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    lon1, lat1, lon2, lat2 = map(math.radians, (lon1, lat1, lon2, lat2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c

# --- UPDATE DATA LENGKAP BALIKPAPAN (VERSI FINAL) ---
location_coords: Dict[str, Tuple[float, float]] = {
    # IT (Integrated Terminal)
    "Depot IT Balikpapan": (116.824915, -1.252753),

    # Hub / Simpang Utama
    "Simpang Karang Jati": (116.833500, -1.248500),
    "Simpang Rapak": (116.835100, -1.241800), 
    "Simpang Gunung Sari": (116.835400, -1.259100),
    "Simpang Balikpapan Baru": (116.855000, -1.235000), 
    "Simpang BP/Sudirman": (116.845000, -1.265000),
    "Simpang Bandara Sepinggan": (116.890000, -1.268000),
    "Simpang Km 5": (116.850000, -1.220000), 
    "Simpang Kariangau": (116.848000, -1.200000), # Percabangan ke Industri

    # SPBU Area Barat & Kota Lama
    "SPBU Karang Anyar": (116.828692, -1.241598),
    "SPBU Kebun Sayur": (116.830500, -1.245000),
    
    # SPBU Area Tengah & Protokol
    "SPBU Gunung Malang": (116.846183, -1.266942),
    "SPBU Gunung Guntur": (116.846764, -1.251218),
    "SPBU Markoni": (116.852000, -1.269000),
    "SPBU MT Haryono (Damai)": (116.865000, -1.245000),
    "SPBU Ruhui Rahayu (Dome)": (116.875000, -1.248000), # TAMBAHAN
    
    # SPBU Area Timur
    "SPBU Stalkuda": (116.865000, -1.268000),
    "SPBU COCO Sepinggan": (116.885000, -1.267000), # TAMBAHAN (Depan Bandara)
    "SPBU Sepinggan Raya": (116.895000, -1.266000),
    "SPBU Batakan": (116.920000, -1.260000),
    "SPBU Manggar": (116.935000, -1.245000), # TAMBAHAN
    "SPBU Teritip": (116.960000, -1.230000),
    
    # SPBU Area Utara (Logistik Kilo)
    "SPBU Km 3 (Soekarno Hatta)": (116.840000, -1.230000), # TAMBAHAN
    "SPBU Km 4 Batu Ampar": (116.845000, -1.225000),
    "SPBU Kariangau (Industri)": (116.820000, -1.180000), # TAMBAHAN
    "SPBU Km 9": (116.860000, -1.190000),
    "SPBU Km 13": (116.865000, -1.170000), # TAMBAHAN
    "SPBU Km 15 (Karang Joang)": (116.870000, -1.150000),
    
    # Jalur Tembus
    "SPBU Syarifuddin Yoes": (116.880000, -1.255000),
}

roads: List[Tuple[str, str, float]] = [
    # Depot -> Rapak Area
    ("Depot IT Balikpapan", "Simpang Karang Jati", 3.0),
    ("Simpang Karang Jati", "SPBU Kebun Sayur", 2.0),
    ("Simpang Karang Jati", "SPBU Karang Anyar", 2.5),
    ("Simpang Karang Jati", "Simpang Rapak", 3.0),
    
    # Rapak -> Menyebar
    ("Simpang Rapak", "SPBU Gunung Guntur", 4.0),
    ("Simpang Rapak", "SPBU Km 3 (Soekarno Hatta)", 3.0), # Ke Utara
    ("Simpang Rapak", "Simpang Gunung Sari", 5.0), # Ke Kota
    
    # Jalur Utara (Kilo)
    ("SPBU Km 3 (Soekarno Hatta)", "Simpang Km 5", 2.0),
    ("Simpang Km 5", "SPBU Km 4 Batu Ampar", 1.5),
    ("Simpang Km 5", "Simpang Kariangau", 8.0), # Menuju percabangan Kariangau
    ("Simpang Kariangau", "SPBU Kariangau (Industri)", 5.0),
    ("Simpang Kariangau", "SPBU Km 9", 4.0),
    ("SPBU Km 9", "SPBU Km 13", 5.0),
    ("SPBU Km 13", "SPBU Km 15 (Karang Joang)", 3.0),
    
    # Jalur Kota & Selatan
    ("Simpang Gunung Sari", "SPBU Gunung Malang", 3.0),
    ("SPBU Gunung Malang", "Simpang BP/Sudirman", 2.0),
    ("Simpang BP/Sudirman", "SPBU Markoni", 3.0),
    ("SPBU Markoni", "SPBU Stalkuda", 4.0),
    
    # Jalur Timur (Pesisir)
    ("SPBU Stalkuda", "Simpang Bandara Sepinggan", 7.0),
    ("Simpang Bandara Sepinggan", "SPBU COCO Sepinggan", 2.0),
    ("SPBU COCO Sepinggan", "SPBU Sepinggan Raya", 2.0),
    ("SPBU Sepinggan Raya", "SPBU Batakan", 5.0),
    ("SPBU Batakan", "SPBU Manggar", 4.0),
    ("SPBU Manggar", "SPBU Teritip", 6.0),
    
    # Jalur Ring Road (Tembus)
    ("Simpang Km 5", "Simpang Balikpapan Baru", 4.0),
    ("Simpang Balikpapan Baru", "SPBU MT Haryono (Damai)", 3.0),
    ("SPBU MT Haryono (Damai)", "SPBU Ruhui Rahayu (Dome)", 4.0),
    ("SPBU Ruhui Rahayu (Dome)", "SPBU Syarifuddin Yoes", 3.0),
    ("SPBU Syarifuddin Yoes", "Simpang Bandara Sepinggan", 4.0),
    
    # Koneksi tambahan
    ("SPBU MT Haryono (Damai)", "SPBU Stalkuda", 5.0),
]

def create_example_graph() -> Graph:
    graph = Graph(average_speed_kmph=AVERAGE_SPEED_KMPH)
    for loc, coord in location_coords.items():
        graph.add_node(loc, coord)
    for from_node, to_node, weight in roads:
        graph.add_edge(from_node, to_node, weight)
    return graph

def compute_multi_stop_route(
    graph: Graph,
    start: str,
    destinations: List[str],
    algorithm: str,
    return_to_start: bool = False,
) -> Tuple[float, List[str]]:
    if not destinations: return 0.0, [start]
    
    valid_dests = [d for d in destinations if d in graph.nodes]
    if not valid_dests: return 0.0, [start]

    solver = graph.dijkstra if algorithm == "Dijkstra" else graph.astar
    best_cost = float("inf")
    best_path: List[str] = []

    limit_perm = itertools.islice(permutations(valid_dests), 120)

    for perm in limit_perm:
        route_nodes = [start] + list(perm)
        if return_to_start:
            route_nodes.append(start)

        total_cost = 0.0
        full_path = [start]
        feasible = True

        for i in range(len(route_nodes) - 1):
            leg_cost, leg_path = solver(route_nodes[i], route_nodes[i + 1])
            if leg_cost == float("inf") or not leg_path:
                feasible = False
                break
            total_cost += leg_cost
            if i == 0:
                full_path = leg_path
            else:
                full_path.extend(leg_path[1:])

        if feasible and total_cost < best_cost:
            best_cost = total_cost
            best_path = full_path

    return best_cost, best_path