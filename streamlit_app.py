from typing import List, Dict, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium

from main import Graph, compute_multi_stop_route, create_example_graph, location_coords
# Import modul peta asli
import map_helper

# --- SETUP PAGE ---
st.set_page_config(page_title="Distribusi BBM Balikpapan", layout="wide")
st.title("Optimasi Jalur Distribusi BBM")

st.markdown(
    """
    Aplikasi ini membandingkan algoritma **Dijkstra** dan **A*** untuk menentukan rute tercepat
    dari depot ke SPBU tujuan. 
    """
)

# --- CACHING DATA PETA ASLI ---
@st.cache_resource(show_spinner=True)
def load_real_map_data():
    """
    Load data OpenStreetMap Balikpapan dan convert ke Graph custom.
    Disimpan dalam cache agar tidak download ulang.
    """
    with st.spinner("Mengunduh data peta Balikpapan (ini hanya dilakukan sekali)..."):
        osm_graph = map_helper.load_balikpapan_graph()
        custom_graph = map_helper.convert_osm_to_custom_graph(osm_graph)
        # Mapping nama lokasi (Depot/SPBU) ke Node ID terdekat di jalan raya
        mapped_nodes = map_helper.get_nearest_nodes(osm_graph, location_coords)
    return osm_graph, custom_graph, mapped_nodes

# --- FUNGSI HELPER LAMA (SIMPLE GRAPH) ---
def _get_simple_graph() -> Graph:
    @st.cache_resource(show_spinner=False)
    def _build() -> Graph:
        return create_example_graph()
    return _build()

def _collect_unique_edges(graph: Graph) -> List[tuple[str, str]]:
    seen = set()
    edges = []
    for source, neighbors in graph.edges.items():
        for target, _ in neighbors:
            key = tuple(sorted((source, target)))
            if key in seen:
                continue
            seen.add(key)
            edges.append((source, target))
    return edges

def _render_simple_graph(graph: Graph, highlight_paths: List[List[str]]):
    edges = _collect_unique_edges(graph)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("Graf Distribusi (Mode Sederhana)")

    for node_a, node_b in edges:
        coord_a = graph.coordinates.get(node_a)
        coord_b = graph.coordinates.get(node_b)
        if not coord_a or not coord_b:
            continue
        ax.plot([coord_a[0], coord_b[0]], [coord_a[1], coord_b[1]], color="#b0b0b0", linewidth=1.5, zorder=1)

    colors = ["#ff1c1c", "#ffa500", "#1c9cff", "#7ac70c", "#8a2be2"]
    for idx, path in enumerate(highlight_paths):
        coords = [graph.coordinates.get(node) for node in path]
        if any(coord is None for coord in coords) or len(coords) < 2:
            continue
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        ax.plot(xs, ys, color=colors[idx % len(colors)], linewidth=3, zorder=2)

    for name, coord in graph.coordinates.items():
        node_type = "SPBU" if name.startswith("SPBU") else ("Depot" if "Depot" in name else "Simpang")
        if node_type == "Depot":
            color = "#009900"
            size = 120
        elif node_type == "SPBU":
            color = "#0066cc"
            size = 90
        else:
            color = "#666666"
            size = 70
        ax.scatter(coord[0], coord[1], s=size, color=color, edgecolors="white", linewidths=0.8, zorder=3)
        ax.text(coord[0], coord[1] + 0.0015, name, fontsize=9, ha="center", va="bottom", zorder=4)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(x=0.1, y=0.12)
    fig.tight_layout()
    return fig


# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Pengaturan Peta")
    map_mode = st.radio("Mode Peta", ["Simple Graph", "Peta Balikpapan"])
    
    st.header("Pengaturan Rute")
    algorithm = st.radio("Algoritma", ["Dijkstra", "A*"])
    
    # Lokasi tersedia (Nama lokasi asli)
    # Gunakan keys dari location_coords agar konsisten di kedua mode
    all_locations_names = sorted(location_coords.keys())
    start_node_name = next((name for name in all_locations_names if "Depot" in name), all_locations_names[0])
    dest_options = [name for name in all_locations_names if name != start_node_name]

    single_destination = st.selectbox("Tujuan tunggal", dest_options, index=0 if dest_options else None)
    multi_destinations = st.multiselect("Tujuan jamak", dest_options)
    enable_multi_stop = st.checkbox("Hitung rute multi tujuan (sekali jalan)")
    return_to_start = st.checkbox("Kembali ke depot setelah distribusi", value=False)

    st.caption("Klik tombol untuk memulai perhitungan.")
    run_single = st.button("Cari Rute")

# --- INITIALIZATION ---
if "highlight_routes" not in st.session_state:
    st.session_state["highlight_routes"] = []
if "route_info" not in st.session_state:
    st.session_state["route_info"] = None

# Logic loading graph berdasarkan mode
active_graph = None
mapped_nodes_dict = None
osm_graph_data = None

if map_mode == "Peta Balikpapan":
    # Load data real
    osm_graph_data, active_graph, mapped_nodes_dict = load_real_map_data()
    # Start Node & Destinations di sini adalah NAMA LOKASI (e.g., "Depot IT...")
    # Nanti perlu diconvert ke Node ID saat perhitungan
else:
    active_graph = _get_simple_graph()
    mapped_nodes_dict = {name: name for name in active_graph.nodes} # Nama node = ID node di simple graph

# --- CALCULATION LOGIC ---
if run_single:
    st.session_state["highlight_routes"] = []
    st.session_state["route_info"] = []
    
    # Tentukan target destinations
    target_dests = []
    if enable_multi_stop and multi_destinations:
        # Multi stop route logic handled inside compute_multi_stop_route
        # Tapi wrapper kita perlu tahu list tujuannya
        pass 
    elif multi_destinations:
        target_dests = multi_destinations # Multiple single routes
    else:
        target_dests = [single_destination] # Single route

    # --- SINGLE / MULTI DESTINATION (INDEPENDENT) ---
    if not enable_multi_stop:
        for dest_name in target_dests:
            # Convert nama lokasi ke ID Node Graph
            start_id = mapped_nodes_dict.get(start_node_name)
            end_id = mapped_nodes_dict.get(dest_name)

            if not start_id or not end_id:
                 st.error(f"Lokasi {start_node_name} atau {dest_name} tidak ditemukan dalam graph.")
                 continue
            
            # Hitung
            solver = active_graph.dijkstra if algorithm == "Dijkstra" else active_graph.astar
            cost, path = solver(start_id, end_id)
            
            if cost == float("inf") or not path:
                st.error(f"Tidak ada rute dari {start_node_name} ke {dest_name}.")
            else:
                st.session_state["highlight_routes"].append(path)
                st.session_state["route_info"].append({
                    "Tujuan": dest_name,
                    "Jarak/Waktu": f"{cost:.2f} menit",
                    "Status": "Berhasil"
                })

    # --- MULTI STOP ROUTE (TSP-like) ---
    else:
        if not multi_destinations:
             st.warning("Pilih minimal satu tujuan untuk rute jamak.")
        else:
            # Kita perlu 'inject' ID node ke fungsi compute_multi_stop_route?
            # Fungsi compute_multi_stop_route menerima graph dan string ID node.
            # Jadi kita harus pass ID node hasil mapping.
            
            # 1. Map nama ke ID
            start_id = mapped_nodes_dict.get(start_node_name)
            dest_ids = [mapped_nodes_dict.get(d) for d in multi_destinations]
            
            # Reverse mapping untuk laporan (ID -> Nama)
            # Karena graph real pakai ID angka, susah dibaca
            # Di simple graph ID = Nama
            id_to_name = {v: k for k, v in mapped_nodes_dict.items()}
            
            try:
                total_cost, path_ids = compute_multi_stop_route(
                    active_graph,
                    start_id,
                    dest_ids,
                    algorithm,
                    return_to_start=return_to_start
                )
                
                if total_cost == float("inf") or not path_ids:
                    st.error("Rute multi tujuan gagal ditemukan.")
                else:
                    st.session_state["highlight_routes"].append(path_ids)
                    
                    # Buat string urutan kunjungan yang mudah dibaca user
                    # Kita hanya bisa menampilkan nama lokasi jika node ID ada di mapped_nodes
                    # (Node jalan biasa tidak punya nama lokasi bisnis)
                    readable_path = []
                    for pid in path_ids:
                         if pid in id_to_name:
                             readable_path.append(id_to_name[pid])
                    # Tampilkan summary sederhana (Start -> Dest 1 -> ... -> Start)
                    route_summary = " -> ".join([start_node_name] + multi_destinations + ([start_node_name] if return_to_start else []))

                    st.session_state["route_info"].append({
                        "Tujuan": "Multi-Stop Route",
                        "Detail": route_summary,
                        "Total Waktu": f"{total_cost:.2f} menit",
                        "Status": "Berhasil"
                    })

            except ValueError as e:
                st.error(str(e))


# --- DISPLAY RESULTS ---
col_result, col_map = st.columns([1, 2])

with col_result:
    st.subheader("Hasil Perhitungan")
    if st.session_state["route_info"]:
        st.table(pd.DataFrame(st.session_state["route_info"]))
    else:
        st.info("Belum ada rute yang dihitung.")

with col_map:
    st.subheader(f"Visualisasi: {map_mode}")

    if map_mode == "Peta Balikpapan":
        # Debug info
        st.write(f"Debug - osm_graph_data loaded: {osm_graph_data is not None}")
        if osm_graph_data is not None:
            st.write(f"Debug - Nodes: {len(osm_graph_data.nodes)}, Edges: {len(osm_graph_data.edges)}")

        if osm_graph_data:
            m = map_helper.create_folium_map(osm_graph_data, locations=location_coords)

            for path in st.session_state["highlight_routes"]:
                route_coords = []
                for node_id in path:
                    nid = int(node_id)
                    if osm_graph_data.has_node(nid):
                        node_data = osm_graph_data.nodes[nid]
                        route_coords.append([node_data['y'], node_data['x']])  # Use list [lat, lon] instead of tuple

                if len(route_coords) > 1:
                    folium.PolyLine(
                        route_coords,
                        color="red",
                        weight=5,
                        opacity=0.8,
                        tooltip=f"Rute ({algorithm})"
                    ).add_to(m)

            st_folium(m, width=700, height=500)
            st.caption("Peta OpenStreetMap Balikpapan (Jalan Raya Nyata)")
        else:
            st.warning("Sedang memuat data peta Balikpapan... Silakan tunggu beberapa detik dan refresh halaman jika diperlukan.")

    else:
        # Simple Map
        fig = _render_simple_graph(active_graph, st.session_state["highlight_routes"])
        st.pyplot(fig)
