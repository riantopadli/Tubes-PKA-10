import streamlit as st
import folium
import random
from streamlit_folium import st_folium
from typing import List

from backend import create_example_graph, compute_multi_stop_route, Graph, location_coords

import navigation
import map as map_utils

def get_scenario_details():
    return {
        "Manual Pilih Sendiri": {
            "targets": [],
            "desc": "Mode Bebas. Anda bisa memilih sendiri SPBU mana saja yang ingin dikunjungi.",
            "insight": "Gunakan mode ini jika ingin mencoba rute buatan sendiri."
        },

        "1. Kehabisan Pertalite Area Padat": {
            "targets": ["SPBU Kebun Sayur", "SPBU Karang Anyar", "SPBU Gunung Malang"],
            "desc": "Kondisi: Pertalite habis di daerah perumahan padat. Banyak angkot dan motor mengantre.",
            "insight": "Fokus: Mengirim cepat ke area macet agar antrean tidak meluber ke jalan raya."
        },

        "2. Kehabisan Pertamax Area Kota": {
            "targets": ["SPBU Markoni", "SPBU MT Haryono (Damai)", "SPBU Ruhui Rahayu (Dome)"],
            "desc": "Kondisi: Stok Pertamax menipis di pusat kota dan area perkantoran. Mobil pribadi butuh BBM.",
            "insight": "Strategi: Prioritas ke jalur jalan besar atau protokol tempat banyak mobil lewat."
        },

        "3. Suplai Terbatas Dekat Depot": {
            "targets": ["SPBU Karang Anyar", "SPBU Markoni", "SPBU Km 3 (Soekarno Hatta)"],
            "desc": "Kondisi: Waktu kerja supir hampir habis. Hanya bisa mengantar ke SPBU yang dekat-dekat saja.",
            "insight": "Efisiensi: Tidak mengambil rute jauh ke pinggiran kota untuk menghemat waktu."
        },

        "4. Pesanan Acak Darurat": {
            "targets": "RANDOM_LIMITED",
            "desc": "Kondisi: Ada panggilan darurat dari 3 SPBU secara acak yang stoknya tiba-tiba kosong.",
            "insight": "Uji Sistem: Melihat apakah aplikasi bisa menangani rute yang tidak terduga."
        },

        "5. Prioritas Jalur Industri Solar": {
            "targets": ["SPBU Kariangau (Industri)", "SPBU Km 13", "SPBU Km 15 (Karang Joang)"],
            "desc": "Kondisi: Stok Solar untuk truk logistik menipis. Harus segera dikirim ke jalur luar kota atau Kilo.",
            "insight": "Rute Lurus: Jalurnya panjang dan lurus, cocok untuk truk besar."
        },

        "6. Jalur Bandara Sepinggan": {
            "targets": ["SPBU Stalkuda", "SPBU COCO Sepinggan", "SPBU Sepinggan Raya"],
            "desc": "Kondisi: Menjaga stok di gerbang udara kota Bandara SAMS. Jalur ini harus selalu tersedia.",
            "insight": "Prioritas: Jalur lebar dan cepat lewat Marsma Iswahyudi, jarang macet parah."
        },

        "7. Bypass Ring Road Hindari Pusat Kota": {
            "targets": ["SPBU MT Haryono (Damai)", "SPBU Ruhui Rahayu (Dome)", "SPBU Syarifuddin Yoes"],
            "desc": "Kondisi: Pusat kota macet total. Truk menggunakan jalur belakang atau Ring Road untuk menjangkau area Sepinggan.",
            "insight": "Logis: Memutar lewat jalan Syarifuddin Yoes adalah cara standar menghindari kemacetan kota."
        },

        "8. Banjir MT Haryono Lewat Pesisir": {
            "targets": ["SPBU Markoni", "SPBU Stalkuda", "SPBU Batakan"],
            "desc": "Kondisi: Jalan Beller banjir tidak bisa lewat. Truk dipaksa lewat Jalan Jend. Sudirman dan Mulawarman pinggir laut.",
            "insight": "Safety: Truk tangki dilarang menerobos banjir. Jalur pesisir adalah opsi paling aman meski memutar."
        },

        "9. Poros Timur Jauh Manggar Teritip": {
            "targets": ["SPBU Batakan", "SPBU Manggar", "SPBU Teritip"],
            "desc": "Kondisi: Pengiriman khusus ke wilayah paling Timur Balikpapan. Sekali jalan untuk mengisi 3 SPBU terjauh.",
            "insight": "Efisiensi: Mengisi berurutan dari Batakan ke Manggar lalu Teritip. Sangat hemat waktu dibanding bolak-balik."
        },

        "10. Permintaan Melonjak Semua SPBU": {
            "targets": "ALL",
            "desc": "Kondisi: Musim mudik lebaran. Semua SPBU butuh pasokan sekaligus.",
            "insight": "Uji Berat: Komputer harus berpikir keras mencari rute paling efisien keliling satu kota."
        }
    }

def _render_map(graph: Graph, highlight_routes: List[List[str]]):
    if not graph.coordinates: return None

    folium_coords = {name: [lat, lon] for name, (lon, lat) in graph.coordinates.items()}

    if folium_coords:
        lats = [c[0] for c in folium_coords.values()]
        lons = [c[1] for c in folium_coords.values()]
        center_map = [sum(lats)/len(lats), sum(lons)/len(lons)]
    else:
        center_map = [-1.25, 116.83]

    m = folium.Map(location=center_map, zoom_start=12)

    seen_edges = set()
    for u, neighbors in graph.edges.items():
        for v, _ in neighbors:
            edge_key = tuple(sorted((u, v)))
            if edge_key not in seen_edges:
                if u in folium_coords and v in folium_coords:
                    folium.PolyLine(
                        [folium_coords[u], folium_coords[v]],
                        color="#6c757d", weight=3, opacity=0.4, dash_array='5,5'
                    ).add_to(m)
                seen_edges.add(edge_key)

    colors = ["#E31B23", "#005DAA", "#5CB85C"]
    for idx, path in enumerate(highlight_routes):
        route_coords = [folium_coords[node] for node in path if node in folium_coords]
        if len(route_coords) > 1:
            folium.PolyLine(
                route_coords, color=colors[idx % len(colors)],
                weight=6, opacity=1.0, tooltip=f"Ritase {idx+1}"
            ).add_to(m)

    for name, coord in folium_coords.items():
        if "Depot" in name:
            icon_c, icon_n = "black", "industry"
        elif "SPBU" in name:
            icon_c, icon_n = "red", "gas-pump"
        else:
            icon_c, icon_n = "gray", "diamond"

        folium.Marker(
            location=coord, popup=name, tooltip=name,
            icon=folium.Icon(color=icon_c, icon=icon_n, prefix="fa")
        ).add_to(m)
    return m


st.set_page_config(page_title="SIMANDIS Pertamina", layout="wide", page_icon="⛽")
st.title("⛽ SIMANDIS (Sistem Manajemen Distribusi BBM)")
st.markdown("**Integrated Terminal Balikpapan** | Dashboard Optimasi Rute Mobil Tangki")

@st.cache_resource
def get_graph(): return create_example_graph()

graph = get_graph()
all_nodes = sorted(list(graph.nodes))
all_spbus = [n for n in all_nodes if "SPBU" in n]
start_node = "Depot IT Balikpapan"

with st.sidebar:
    st.header("🎛️ Operasional Ritase")
    navigation_mode = st.radio("Mode Navigasi", ["Simple Graph", "Balikpapan Map"], horizontal=False)
    algo = st.radio("Metode Hitung", ["Dijkstra (Jarak Terpendek)", "A* (Heuristik)"], horizontal=True)
    st.divider()

    scenario_data = get_scenario_details()

    def update_scenario_state():
        sel = st.session_state.scenario_selector
        data = scenario_data[sel]

        if data["targets"] == "ALL":
            st.session_state.selected_targets = all_spbus
        elif data["targets"] == "RANDOM_LIMITED":
            st.session_state.selected_targets = random.sample(all_spbus, 3) if len(all_spbus) >= 3 else all_spbus
        elif sel == "Manual (Pilih Sendiri)":
            st.session_state.selected_targets = []
        else:
            valid_targets = [t for t in data["targets"] if t in all_spbus]
            st.session_state.selected_targets = valid_targets

    selected_scenario = st.selectbox(
        "Pilih Skenario Lapangan:",
        list(scenario_data.keys()),
        key="scenario_selector", on_change=update_scenario_state
    )

    desc = scenario_data[selected_scenario]["desc"]
    st.info(f"{desc}")

    if "selected_targets" not in st.session_state: st.session_state.selected_targets = []

    targets = st.multiselect("Lembaga Penyalur (SPBU):", options=all_spbus, key="selected_targets")
    enable_multi_stop = st.checkbox("Hitung rute multi tujuan (sekali jalan)")
    round_trip = st.checkbox("Kembali ke Depot (Round Trip)?", value=True)

    st.divider()

    if st.button("🚀 Kalkulasi Rute", type="primary", use_container_width=True):
        if targets:
            with st.spinner("Menghitung rute optimal..."):
                try:
                    algo_name = algo.split(" ")[0]

                    if navigation_mode == "Balikpapan Map":
                        st.session_state.nav_result = None
                        st.session_state.info = None

                        if len(targets) == 1 or not enable_multi_stop:
                            if len(targets) == 1:
                                nav_result = navigation.navigate_real_time_route(
                                    start_location=start_node,
                                    destinations=targets,
                                    algorithm=algo_name,
                                    return_to_start=round_trip
                                )
                                st.session_state.nav_result = nav_result
                                st.session_state.info = {
                                    "cost": nav_result['cost'],
                                    "path": nav_result['readable_path'],
                                    "scenario": selected_scenario
                                }
                            else:
                                route_results = []
                                total_cost = 0
                                combined_paths = []
                                for target in targets:
                                    single_result = navigation.navigate_real_time_route(
                                        start_location=start_node,
                                        destinations=[target],
                                        algorithm=algo_name,
                                        return_to_start=round_trip
                                    )
                                    route_results.append(single_result)
                                    total_cost += single_result['cost']
                                    combined_paths.extend(single_result['readable_path'])

                                st.session_state.nav_result = route_results
                                unique_waypoints = []
                                seen = set()
                                for path in combined_paths:
                                    if path not in seen:
                                        unique_waypoints.append(path)
                                        seen.add(path)
                                st.session_state.info = {
                                    "cost": total_cost,
                                    "path": unique_waypoints,
                                    "scenario": selected_scenario
                                }
                        else:
                            nav_result = navigation.navigate_multi_stop_route(
                                start_location=start_node,
                                destinations=targets,
                                algorithm=algo_name,
                                return_to_start=round_trip
                            )
                            st.session_state.nav_result = nav_result
                            st.session_state.info = {
                                "cost": nav_result['cost'],
                                "path": nav_result['readable_path'],
                                "scenario": selected_scenario
                            }
                    else:
                        st.session_state.routes = []
                        st.session_state.info = None

                        cost, path = compute_multi_stop_route(graph, start_node, targets, algo_name, return_to_start=round_trip)
                        st.session_state.routes = [path]
                        st.session_state.info = {"cost": cost, "path": path, "scenario": selected_scenario}
                except Exception as e: st.error(f"Error: {e}")
        else: st.warning("Pilih tujuan dulu.")

col1, col2 = st.columns([2, 1])

if "routes" not in st.session_state: st.session_state.routes = []
if "info" not in st.session_state: st.session_state.info = None
if "nav_result" not in st.session_state: st.session_state.nav_result = None

with col1:
    st.subheader(f"🗺️{navigation_mode}")

    if navigation_mode == "Balikpapan Map":
        if st.session_state.nav_result:
            nav_map = navigation.create_navigation_map(st.session_state.nav_result, targets=targets)
            st_folium(nav_map, width="100%", height=550)
            st.caption("🗺️ **Real-Time Navigation**: Rute mengikuti jalan nyata Balikpapan dari OpenStreetMap")
        else:
            st.info("Pilih tujuan dan klik 'Cari Rute' untuk melihat navigasi real-time")
            osm_graph, _, _ = navigation.get_real_time_graph()
            empty_map = map_utils.create_folium_map(osm_graph, locations=location_coords)
            st_folium(empty_map, width="100%", height=550)
    else:
        map_viz = _render_map(graph, st.session_state.routes)
        if map_viz: st_folium(map_viz, width="100%", height=550)
        st.caption("📊 **Simple Graph**: Representasi graf jaringan distribusi sederhana")

with col2:
    st.subheader("📊 Statistik Ritase")
    res = st.session_state.info
    if res:
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Est. Waktu Putaran", f"{res['cost']:.1f} min")
        kpi2.metric("Titik Drop", len(targets))

        sel_scen = res.get("scenario", "Manual")
        if sel_scen in scenario_data:
            st.success(scenario_data[sel_scen]["insight"])

        path = res['path']

        st.markdown(f"🏭 **BERANGKAT**: {path[0]}")

        targets_in_path = [node for node in path[1:-1] if node in targets]
        for target in targets_in_path:
            st.markdown(f"⛽ **BONGKAR BBM**: {target}")

        if len(path) > 1:
            st.markdown(f"🏁 **TIBA**: {path[-1]}")
    else:
        st.info("Pilih skenario di panel kiri.")
