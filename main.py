import math
from itertools import permutations
from typing import Dict, List, Optional, Set, Tuple


class Graph:
    def __init__(self, average_speed_kmph: float = 30.0):
        # adjacency list: node -> list of (tetangga, bobot menit)
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
        self.edges[to_node].append((from_node, weight))  # graf dua arah

    def dijkstra(self, start: str, end: str) -> Tuple[float, List[str]]:
        import heapq

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
        import heapq

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

    def __str__(self) -> str:
        lines = []
        for node, neighbors in self.edges.items():
            lines.append(f"{node}: {neighbors}")
        return "\n".join(lines)


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


location_coords: Dict[str, Tuple[float, float]] = {
    # Node Awal
    "Depot IT Balikpapan": (116.824915, -1.252753),
    
    # Node Simpang (Penghubung) - Nama disesuaikan lokasi asli
    "Simpang Karang Jati": (116.833500, -1.248500), # Pintu keluar area kilang/depot
    "Simpang Tugu Adipura": (116.829500, -1.244200), # Belokan ke Karang Anyar
    "Simpang Rapak": (116.835100, -1.241800),       # Simpang utama (Rawan macet)
    "Simpang Gunung Sari": (116.835400, -1.259100), # Arah ke Gunung Malang
    "Simpang Dr. Sutomo": (116.841000, -1.250100),  # Jalan potong ke Gunung Guntur
    
    # Node Tujuan (SPBU)
    "SPBU Karang Anyar": (116.828692, -1.241598),
    "SPBU Gunung Malang": (116.846183, -1.266942),
    "SPBU Gunung Guntur": (116.846764, -1.251218),
}

roads: List[Tuple[str, str, float]] = [
    # --- Jalur Keluar dari Depot ---
    ("Depot IT Balikpapan", "Simpang Karang Jati", 1.2),
    
    # --- Jalur ke SPBU Karang Anyar ---
    ("Simpang Karang Jati", "Simpang Tugu Adipura", 0.8),
    ("Simpang Tugu Adipura", "SPBU Karang Anyar", 0.5),
    
    # --- Jalur Utama (Karang Jati ke Rapak) ---
    ("Simpang Karang Jati", "Simpang Rapak", 1.0),
    
    # --- Jalur ke SPBU Gunung Malang ---
    ("Simpang Rapak", "Simpang Gunung Sari", 2.1), # Lewat Jl. Jend A. Yani
    ("Simpang Gunung Sari", "SPBU Gunung Malang", 1.8), # Lewat Jl. Mayjend Sutoyo
    
    # --- Jalur ke SPBU Gunung Guntur ---
    # Opsi 1: Lewat Rapak -> Panjaitan
    ("Simpang Rapak", "SPBU Gunung Guntur", 2.5), # Lewat Jl. S. Parman/Panjaitan
    
    # Opsi 2: Lewat Jalan Dr. Sutomo (Alternatif)
    ("Simpang Karang Jati", "Simpang Dr. Sutomo", 1.5), 
    ("Simpang Dr. Sutomo", "SPBU Gunung Guntur", 0.7),
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
    if not destinations:
        return 0.0, [start]

    for dest in destinations:
        if dest not in graph.nodes:
            raise ValueError(f"Tujuan '{dest}' tidak ditemukan dalam graf.")

    solver = graph.dijkstra if algorithm == "Dijkstra" else graph.astar

    best_cost = float("inf")
    best_path: List[str] = []

    for perm in permutations(destinations):
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
def main() -> None:
    graph = create_example_graph()
    depot = "Depot IT Balikpapan"
    available = sorted(node for node in graph.nodes if node != depot)
    print("Daftar tujuan yang tersedia (masukkan nomor):")
    for idx, name in enumerate(available, start=1):
        print(f" {idx}. {name}")

    print(
        "\nMasukkan angka tujuan (pisahkan dengan koma).\n"
        "Tekan Enter tanpa input untuk menggunakan contoh default:"
    )
    user_input = input("Pilihan: ").strip()
    if user_input:
        choices: List[int] = []
        for raw in user_input.split(","):
            raw = raw.strip()
            if not raw:
                continue
            if not raw.isdigit():
                print(f"[Peringatan] '{raw}' bukan angka valid dan diabaikan.")
                continue
            idx = int(raw)
            if 1 <= idx <= len(available):
                choices.append(idx - 1)
            else:
                print(f"[Peringatan] angka {idx} di luar rentang dan diabaikan.")
        destinations = [available[i] for i in choices]
    else:
        destinations = [
            "SPBU Karang Anyar",
            "SPBU Gunung Malang",
            "SPBU Gunung Guntur",
        ]

    valid_destinations = []
    for dest in destinations:
        if dest == depot:
            print(f"[Peringatan] {dest} adalah titik awal dan diabaikan.")
        else:
            valid_destinations.append(dest)

    if not valid_destinations:
        print("Tidak ada tujuan valid yang dipilih. Program selesai.")
        return

    for algorithm in ("Dijkstra", "A*"):
        solver = graph.dijkstra if algorithm == "Dijkstra" else graph.astar
        print(f"\n=== {algorithm} ===")
        for destination in valid_destinations:
            cost, path = solver(depot, destination)
            if cost == float("inf") or not path:
                print(f"{destination}: tidak ada rute.")
            else:
                print(f"{destination}: {path} | total waktu {cost:.1f} menit")


if __name__ == "__main__":
    main()
