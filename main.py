import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from typing import List, Tuple

# Mengimpor class dan fungsi dari main.py yang Anda buat
from main import create_example_graph, compute_multi_stop_route, Graph

# --- FUNGSI HELPER VISUALISASI ---

def _render_map(graph: Graph, highlight_routes: List[List[str]]):
    """
    Render peta interaktif menggunakan Folium.
    Menangani konversi koordinat dari (Lon, Lat) user ke (Lat, Lon) Folium.
    """
    if not graph.coordinates:
        return None

    # 1. Konversi Koordinat: Data Anda (Lon, Lat) -> Folium (Lat, Lon)
    folium_coords = {}
    for name, (lon, lat) in graph.coordinates.items():
        folium_coords[name] = [lat, lon]

    # Hitung titik tengah peta
    lats = [c[0] for c in folium_coords.values()]
    lons = [c[1] for c in folium_coords.values()]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Inisialisasi Map (Zoom disesuaikan untuk area Balikpapan)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    # 2. Gambar Jalur (Edges) Tipis (Jaringan Jalan)
    # Kita ambil unique edges agar tidak menggambar dobel
    seen_edges = set()
    for u, neighbors in graph.edges.items():
        for v, _ in neighbors:
            edge_key = tuple(sorted((u, v)))
            if edge_key not in seen_edges:
                if u in folium_coords and v in folium_coords:
                    folium.PolyLine(
                        [folium_coords[u], folium_coords[v]],
                        color="#888888",
                        weight=2,
                        opacity=0.4,
                        dash_array='5, 5'
                    ).add_to(m)
                seen_edges.add(edge_key)

    # 3. Gambar Rute Terpilih (Highlight)
    # Warna rute berbeda-beda jika ada multiple routes (looping warna)
    colors = ["#FF0000", "#0000FF", "#FFA500", "#800080"] 
    
    for idx, path in enumerate(highlight_routes):
        route_coords = []
        for node in path:
            if node in folium_coords:
                route_coords.append(folium_coords[node])
        
        if len(route_coords) > 1:
            folium.PolyLine(
                route_coords, 
                color=colors[idx % len(colors)], 
                weight=6, 
                opacity=0.9,
                tooltip=f"Jalur {idx+1}"
            ).add_to(m)

    # 4. Gambar Marker (Titik Lokasi)
    for name, coord in folium_coords.items():
        # Logika Ikon berdasarkan nama lokasi
        if "Depot" in name:
            icon_color = "green"
            icon_name = "warehouse"
        elif "SPBU" in name:
            icon_color = "red"
            icon_name = "gas-pump"
        else:
            icon_color = "blue"
            icon_name = "road" # Simpang

        folium.Marker(
            location=coord,
            popup=name,
            tooltip=name,
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
        ).add_to(m)

    return m

# --- HALAMAN UTAMA STREAMLIT ---

st.set_page_config(page_title="Distribusi BBM Balikpapan", layout="wide")

st.title("🚛 Optimasi Rute Distribusi BBM")
st.caption("Implementasi Algoritma Dijkstra & A* pada Peta Digital Balikpapan")


# Load Graf dari main.py
# Menggunakan cache agar graf tidak dibuat ulang setiap kali klik tombol
@st.cache_resource
def get_cached_graph():
    return create_example_graph()

graph = get_cached_graph()

# Siapkan data untuk Sidebar
all_locations = sorted(graph.nodes)
# Deteksi otomatis node Depot (yang mengandung kata "Depot")
start_node = next((n for n in all_locations if "Depot" in n), all_locations[0])
dest_options = [n for n in all_locations if n != start_node]

# Inisialisasi state untuk menyimpan hasil rute agar tidak hilang saat re-render map
if "highlight_routes" not in st.session_state:
    st.session_state["highlight_routes"] = []
if "route_info" not in st.session_state:
    st.session_state["route_info"] = None

with st.sidebar:
    st.header("⚙️ Konfigurasi")
    
    algorithm = st.radio("Pilih Algoritma", ["Dijkstra", "A*"], help="A* menggunakan heuristic jarak garis lurus (Haversine).")
    
    st.subheader("Tujuan Distribusi")
    multi_destinations = st.multiselect(
        "Pilih SPBU Tujuan:", 
        options=dest_options,
        default=[dest_options[0]] if dest_options else None
    )
    
    return_to_depot = st.checkbox("Kembali ke Depot setelah selesai?", value=True)
    
    st.markdown("---")
    if st.button("🚀 Hitung Rute Terbaik", type="primary"):
        if not multi_destinations:
            st.warning("Mohon pilih minimal satu tujuan.")
        else:
            try:
                # Memanggil fungsi compute dari main.py
                cost, path = compute_multi_stop_route(
                    graph, 
                    start_node, 
                    multi_destinations, 
                    algorithm, 
                    return_to_start=return_to_depot
                )
                
                # Simpan hasil ke session state
                st.session_state["highlight_routes"] = [path]
                st.session_state["route_info"] = {
                    "cost": cost,
                    "path": path,
                    "algorithm": algorithm
                }
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

# Layout: Kiri (Peta), Kanan (Detail)
col_map, col_details = st.columns([2, 1])

with col_map:
    st.subheader("Peta Rute")
    map_obj = _render_map(graph, st.session_state["highlight_routes"])
    if map_obj:
        st_folium(map_obj, width="100%", height=500)
    else:
        st.warning("Data koordinat tidak ditemukan.")

with col_details:
    st.subheader("Detail Perjalanan")
    
    if st.session_state["route_info"]:
        info = st.session_state["route_info"]
        
        # Kartu ringkasan
        st.info(f"**Total Waktu:** {info['cost']:.2f} menit")
        st.caption(f"Algoritma: {info['algorithm']}")
        
        # Timeline perjalanan
        st.markdown("### 📍 Urutan Kunjungan")
        path = info['path']
        
        for i in range(len(path)):
            node = path[i]
            # Menghitung biaya per leg (ruas jalan)
            time_cost = 0
            if i > 0:
                prev = path[i-1]
                # Cari bobot edge langsung dari graph
                # Karena graph.edges structure: dict[u] -> list[(v, w)]
                neighbors = graph.edges.get(prev, [])
                for neighbor, weight in neighbors:
                    if neighbor == node:
                        time_cost = weight
                        break
            
            icon = "🏁" if i == len(path)-1 else ("🏠" if i == 0 else "⛽")
            if "Simpang" in node: icon = "🚦"
            
            if i == 0:
                st.markdown(f"**{icon} Mulai**: {node}")
            else:
                st.markdown(f"⬇️ *({time_cost} min)*")
                st.markdown(f"**{icon} {node}**")
                
    else:
        st.markdown("*Silakan pilih tujuan dan tekan tombol Hitung untuk melihat detail.*")