import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from typing import List, Tuple

from backend import create_example_graph, compute_multi_stop_route, Graph

def _render_map(graph: Graph, highlight_routes: List[List[str]]):
    """Render interactive map with Folium, converting coordinates to Folium format."""
    if not graph.coordinates:
        return None

    folium_coords = {name: [lat, lon] for name, (lon, lat) in graph.coordinates.items()}

    lats = [c[0] for c in folium_coords.values()]
    lons = [c[1] for c in folium_coords.values()]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    seen_edges = set()
    for u, neighbors in graph.edges.items():
        for v, _ in neighbors:
            edge_key = tuple(sorted((u, v)))
            if edge_key not in seen_edges and u in folium_coords and v in folium_coords:
                folium.PolyLine(
                    [folium_coords[u], folium_coords[v]],
                    color="#888888",
                    weight=2,
                    opacity=0.4,
                    dash_array='5, 5'
                ).add_to(m)
                seen_edges.add(edge_key)

    colors = ["#FF0000", "#0000FF", "#FFA500", "#800080"]
    for idx, path in enumerate(highlight_routes):
        route_coords = [folium_coords[node] for node in path if node in folium_coords]
        if len(route_coords) > 1:
            folium.PolyLine(
                route_coords,
                color=colors[idx % len(colors)],
                weight=6,
                opacity=0.9,
                tooltip=f"Jalur {idx+1}"
            ).add_to(m)

    for name, coord in folium_coords.items():
        if "Depot" in name:
            icon_color, icon_name = "green", "warehouse"
        elif "SPBU" in name:
            icon_color, icon_name = "red", "gas-pump"
        else:
            icon_color, icon_name = "blue", "road"

        folium.Marker(
            location=coord,
            popup=name,
            tooltip=name,
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
        ).add_to(m)

    return m

st.set_page_config(page_title="Distribusi BBM Balikpapan", layout="wide")

st.title("🚛 Optimasi Rute Distribusi BBM")
st.caption("Implementasi Algoritma Dijkstra & A* pada Peta Digital Balikpapan")

@st.cache_resource
def get_cached_graph():
    return create_example_graph()

graph = get_cached_graph()

all_locations = sorted(graph.nodes)
start_node = next((n for n in all_locations if "Depot" in n), all_locations[0])
dest_options = [n for n in all_locations if n != start_node]
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
                cost, path = compute_multi_stop_route(
                    graph,
                    start_node,
                    multi_destinations,
                    algorithm,
                    return_to_start=return_to_depot
                )

                st.session_state["highlight_routes"] = [path]
                st.session_state["route_info"] = {
                    "cost": cost,
                    "path": path,
                    "algorithm": algorithm
                }
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")

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
        
        st.info(f"**Total Waktu:** {info['cost']:.2f} menit")
        st.caption(f"Algoritma: {info['algorithm']}")

        st.markdown("### 📍 Urutan Kunjungan")
        path = info['path']
        
        for i in range(len(path)):
            node = path[i]
            time_cost = 0
            if i > 0:
                prev = path[i-1]
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
