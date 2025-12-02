import osmnx as ox
import networkx as nx
import folium
from main import Graph, location_coords

def load_balikpapan_graph(place_name="Balikpapan, Indonesia"):
    """
    Download dan load graph jalan raya Balikpapan dari OpenStreetMap.
    Menggunakan simplify=True agar graph lebih ringan.
    """
    # Download graph jalan (drive)
    # simplify=True menggabungkan edge lurus menjadi satu, mengurangi jumlah node drastis
    G = ox.graph_from_place(place_name, network_type="drive", simplify=True)
    
    # Tambahkan atribut speed dan travel_time jika tidak ada
    # Ini penting untuk perhitungan bobot waktu
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    return G

def convert_osm_to_custom_graph(osm_graph):
    """
    Konversi graph OSMnx (MultiDiGraph) ke format class Graph custom kita.
    """
    custom_graph = Graph()
    
    # 1. Tambahkan Nodes
    # Di OSMnx, node diidentifikasi dengan ID (int).
    # Kita simpan koordinatnya juga.
    for node_id, data in osm_graph.nodes(data=True):
        # OSMnx menyimpan y=lat, x=lon
        custom_graph.add_node(str(node_id), (data['x'], data['y']))
        
    # 2. Tambahkan Edges
    # OSMnx graph adalah MultiDiGraph (bisa ada multiple edge antar 2 node)
    # Kita ambil yang terpendek/tercepat jika ada duplikat
    for u, v, data in osm_graph.edges(data=True):
        weight = 0.0
        # Prioritas pakai travel_time (detik) -> convert ke menit
        if 'travel_time' in data:
            weight = data['travel_time'] / 60.0
        # Jika tidak ada travel_time, hitung manual dari length (m) / speed (m/s)
        elif 'length' in data:
            length_km = data['length'] / 1000.0
            # Default speed 30 km/h jika tidak ada data
            speed_kmph = data.get('speed_kph', 30.0)
            if isinstance(speed_kmph, list):
                speed_kmph = float(speed_kmph[0])
            weight = (length_km / speed_kmph) * 60.0
            
        # Hindari weight 0 atau negatif
        weight = max(weight, 0.01)
        
        # Add edge satu arah (karena OSMnx directed)
        # Class Graph kita menyimpan edge dua arah di method add_edge,
        # tapi di sini kita perlu kontrol manual karena jalan bisa one-way.
        # Jadi kita modifikasi sedikit cara insertnya agar sesuai directed graph
        # TAPI: Graph custom di main.py implementasinya:
        # self.edges[from_node].append((to_node, weight))
        # self.edges[to_node].append((from_node, weight)) <-- INI MEMBUAT JADI UNDIRECTED/BIDIRECTIONAL
        #
        # Masalah: Jalan di kota banyak yang satu arah.
        # Solusi Sementara: Kita ikuti struktur Graph yang ada (undirected) 
        # ATAU kita hanya masukkan edge sesuai arah OSM, 
        # tapi kita harus akses properti internal 'edges' secara langsung 
        # supaya tidak otomatis bolak-balik jika method add_edge memaksa bolak-balik.
        
        u_str, v_str = str(u), str(v)
        
        # Manual insertion untuk kontrol arah (Directed)
        if u_str not in custom_graph.edges:
            custom_graph.edges[u_str] = []
        custom_graph.edges[u_str].append((v_str, weight))
        
        # Pastikan node tujuan terdaftar di keys
        if v_str not in custom_graph.edges:
            custom_graph.edges[v_str] = []

    return custom_graph

def get_nearest_nodes(osm_graph, locations):
    """
    Mencari node jalan terdekat untuk setiap lokasi (Depot/SPBU).
    Returns dict: {'Nama Lokasi': 'Node_ID'}
    """
    mapped_nodes = {}
    for name, (lon, lat) in locations.items():
        # ox.distance.nearest_nodes butuh (X, Y) yaitu (Lon, Lat)
        nearest_node = ox.distance.nearest_nodes(osm_graph, lon, lat)
        mapped_nodes[name] = str(nearest_node)
    return mapped_nodes

def create_folium_map(osm_graph, path_nodes=None, locations=None):
    """
    Membuat peta Folium.
    - osm_graph: Graph OSMnx asli (untuk plotting geometri jalan jika perlu, 
      tapi agar ringan kita pakai TileLayer standar saja).
    - path_nodes: List of node IDs (str) yang membentuk rute.
    - locations: Dict koordinat asli {'Nama': (lon, lat)} untuk marker.
    """
    # Pusat peta rata-rata dari node graph atau default Balikpapan
    center_lat = -1.25
    center_lon = 116.83
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 1. Gambar Marker Lokasi Penting (Depot/SPBU)
    if locations:
        for name, (lon, lat) in locations.items():
            color = "green" if "Depot" in name else "blue"
            icon = folium.Icon(color=color, icon="gas-pump", prefix="fa")
            folium.Marker(
                location=[lat, lon],
                popup=name,
                tooltip=name,
                icon=icon
            ).add_to(m)
            
    # 2. Gambar Rute (Jika ada)
    if path_nodes and len(path_nodes) > 1:
        # Kita perlu koordinat (lat, lon) untuk setiap node dalam path
        route_coords = []
        for node_id in path_nodes:
            # Node ID di custom graph adalah string, di osm_graph int
            nid = int(node_id)
            if osm_graph.has_node(nid):
                node_data = osm_graph.nodes[nid]
                route_coords.append((node_data['y'], node_data['x']))
        
        # Gambar garis rute
        folium.PolyLine(
            route_coords,
            color="red",
            weight=5,
            opacity=0.8,
            tooltip="Rute Terpilih"
        ).add_to(m)
        
        # Fit bounds agar rute terlihat semua
        if route_coords:
            m.fit_bounds(route_coords)
            
    return m
